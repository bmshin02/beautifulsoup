import types

import pytest

from . import (
    HTML5LIB_PRESENT,
    LXML_PRESENT,
    SoupTest,
)
from bs4 import BeautifulSoup
from bs4.element import (
    CData,
    Comment,
    Doctype,
    NavigableString,
    ProcessingInstruction,
    Tag,
    XMLProcessingInstruction,
)

PARSERS = ["html.parser"]
if LXML_PRESENT:
    PARSERS += ["lxml", "xml"]
if HTML5LIB_PRESENT:
    PARSERS += ["html5lib"]


class TestSoupIterator(SoupTest):
    def test_yields_tags_in_document_order(self):
        # Every tag comes out once, each one before its children
        # (depth-first, pre-order). The soup itself is not a node of
        # the document, so it is not yielded.
        soup = BeautifulSoup(
            "<html><body><div><p><b></b><i></i></p></div><ul><li></li></ul>"
            "</body></html>",
            "html.parser",
        )
        names = [node.name for node in soup]
        assert names == ["html", "body", "div", "p", "b", "i", "ul", "li"]
        assert all(isinstance(node, Tag) for node in soup)
        assert soup not in list(iter(soup))

        # Only the soup changed: iterating a Tag still gives its
        # direct children, like it always has.
        assert [child.name for child in soup.body] == ["div", "ul"]

    def test_yields_text_nodes(self):
        # Text is a node too. Text between tags, text inside nested
        # tags, and whitespace-only text each come out once, in the
        # place they appear in the document.
        soup = BeautifulSoup(
            "<p>Hello <b>big</b> world</p>\n<p>bye</p>", "html.parser"
        )
        strings = [node for node in soup if isinstance(node, NavigableString)]
        assert strings == ["Hello ", "big", " world", "\n", "bye"]
        assert [s.parent.name for s in strings] == ["p", "b", "p", "[document]", "p"]

        # Tags and strings are interleaved in document order.
        assert [
            node.name if isinstance(node, Tag) else str(node) for node in soup
        ] == ["p", "Hello ", "b", "big", " world", "\n", "p", "bye"]

    def test_yields_special_strings(self):
        # Doctypes, comments, CDATA sections and processing
        # instructions are all nodes, and each keeps its own class.
        soup = BeautifulSoup(
            "<!DOCTYPE html><p>hi<!--note--><![CDATA[raw]]><?php echo 1 ?></p>",
            "html.parser",
        )
        assert [(type(node), str(node)) for node in soup] == [
            (Doctype, "html"),
            (Tag, "<p>hi<!--note--><![CDATA[raw]]><?php echo 1 ?></p>"),
            (NavigableString, "hi"),
            (Comment, "note"),
            (CData, "raw"),
            (ProcessingInstruction, "php echo 1 ?"),
        ]

    @pytest.mark.skipif(not LXML_PRESENT, reason="lxml seems not to be present")
    def test_yields_xml_nodes(self):
        # An XML document: a processing instruction before the root,
        # namespaced tags, an empty-element tag and a comment.
        soup = BeautifulSoup(
            '<?xml version="1.0"?><?xml-stylesheet href="s.css"?>'
            '<rss xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<item><dc:creator>Ann</dc:creator><link/><!--c--></item></rss>",
            "xml",
        )
        nodes = list(soup)
        assert [type(node) for node in nodes] == [
            XMLProcessingInstruction,
            Tag,
            Tag,
            Tag,
            NavigableString,
            Tag,
            Comment,
        ]
        creator = nodes[3]
        assert (creator.prefix, creator.name) == ("dc", "creator")
        assert nodes[5].name == "link" and nodes[5].is_empty_element

    @pytest.mark.parametrize("features", PARSERS)
    def test_iteration_is_lazy(self, features):
        soup = BeautifulSoup("<div><p>one</p><p>two</p></div>", features)

        # iter(soup) is a generator, not a list or an iterator over
        # one: it hands out one node per next() call.
        nodes = iter(soup)
        assert isinstance(nodes, types.GeneratorType)
        first = next(nodes)
        assert isinstance(first, Tag)

        # Because nothing was collected in advance, a node added to
        # the tree after iteration started is still visited.
        soup.find_all("p")[-1].append(soup.new_tag("em"))
        assert "em" in [getattr(node, "name", None) for node in nodes]

        # Each loop starts over, and every parser's tree gives the
        # same nodes, in the same order, as Tag.descendants.
        assert list(soup) == list(soup.descendants)
        assert list(soup) == list(soup)

        # An empty document has no nodes. (html5lib always builds
        # <html><head><body>, so it gets those three.)
        empty = BeautifulSoup("", features)
        expected = ["html", "head", "body"] if features == "html5lib" else []
        assert [node.name for node in empty] == expected
