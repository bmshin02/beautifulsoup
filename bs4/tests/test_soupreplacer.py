import pytest

from . import (
    LXML_PRESENT,
    SoupTest,
)
from bs4 import BeautifulSoup
from bs4.filter import SoupReplacer

# html5lib is left out because it doesn't support SoupReplacer.
PARSERS = ["html.parser"]
if LXML_PRESENT:
    PARSERS += ["lxml", "xml"]


class TestSoupReplacer(SoupTest):
    @pytest.mark.parametrize("features", PARSERS)
    def test_replaces_tags_during_parsing(self, features):
        # Every <b> tag is created as a <blockquote> tag instead, and
        # keeps its attributes and contents.
        replacer = SoupReplacer("b", "blockquote")
        soup = BeautifulSoup(
            '<p><b id="first">bold</b> and <b>more</b></p>',
            features,
            replacer=replacer,
        )
        assert soup.find_all("b") == []

        quotes = soup.find_all("blockquote")
        assert [quote.string for quote in quotes] == ["bold", "more"]
        assert quotes[0]["id"] == "first"

    @pytest.mark.parametrize("features", PARSERS)
    def test_end_tag_closes_replaced_tag(self, features):
        # The end tag in the document is still </b>. It has to close
        # the <blockquote>, or the text after it ends up inside.
        replacer = SoupReplacer("b", "blockquote")
        soup = BeautifulSoup("<p><b>x</b>y</p>", features, replacer=replacer)

        quote = soup.blockquote
        assert quote.contents == ["x"]
        assert quote.next_sibling == "y"
        assert quote.parent.name == "p"

    @pytest.mark.parametrize("features", PARSERS)
    def test_sets_attributes_during_parsing(self, features):
        # attrs are added to every matching tag, replacing any value
        # the document already had. Other tags are left alone.
        replacer = SoupReplacer("p", "p", attrs={"class": "test"})
        soup = BeautifulSoup(
            '<div><p class="old intro">a</p><p>b</p><span>c</span></div>',
            features,
            replacer=replacer,
        )
        paragraphs = soup.find_all("p")
        assert [p.get_attribute_list("class") for p in paragraphs] == [
            ["test"],
            ["test"],
        ]
        assert soup.span.attrs == {}


class TestSoupReplacerXformers(SoupTest):
    """Milestone 3: SoupReplacer(name_xformer=, attrs_xformer=, xformer=)."""

    @pytest.mark.parametrize("features", PARSERS)
    def test_name_xformer_renames_tags(self, features):
        # The end tag in the document is still </b>, so the text after
        # it must end up outside the renamed tag.
        b_to_blockquote = SoupReplacer(
            name_xformer=lambda tag: "blockquote" if tag.name == "b" else tag.name
        )
        soup = BeautifulSoup(
            '<p><b id="first">bold</b>after<i>it</i></p>',
            features,
            replacer=b_to_blockquote,
        )
        assert soup.find_all("b") == []
        quote = soup.blockquote
        assert quote.contents == ["bold"]
        assert quote["id"] == "first"
        assert quote.next_sibling == "after"
        assert quote.parent.name == "p"
        assert soup.i.string == "it"

    @pytest.mark.parametrize("features", PARSERS)
    def test_attrs_xformer_replaces_attributes(self, features):
        # Whatever attrs_xformer returns becomes the tag's attributes.
        def p_class_test(tag):
            if tag.name == "p":
                return {"class": ["test"]}
            return tag.attrs

        soup = BeautifulSoup(
            '<div id="d"><p class="old" title="t">a</p><p>b</p></div>',
            features,
            replacer=SoupReplacer(attrs_xformer=p_class_test),
        )
        assert [p.attrs for p in soup.find_all("p")] == [
            {"class": ["test"]},
            {"class": ["test"]},
        ]
        assert soup.div.attrs == {"id": "d"}

    @pytest.mark.parametrize("features", PARSERS)
    def test_xformer_side_effects(self, features):
        # The example from the assignment: xformer changes the tag in
        # place and returns nothing.
        def remove_class_attr(tag):
            if "class" in tag.attrs:
                del tag.attrs["class"]

        soup = BeautifulSoup(
            '<div class="a" id="d"><p class="b c">x</p><span class="e">y</span></div>',
            features,
            replacer=SoupReplacer(xformer=remove_class_attr),
        )
        assert soup.find_all(class_=True) == []
        assert soup.div["id"] == "d"
        assert soup.p.string == "x"

    @pytest.mark.parametrize("features", PARSERS)
    def test_xformer_sees_finished_subtree(self, features):
        # Tags are transformed when they close, so xformer can look at
        # everything inside the tag, including nested tags.
        def count_words(tag):
            if tag.name == "p":
                tag["data-words"] = str(len(tag.get_text().split()))

        soup = BeautifulSoup(
            "<div><p>one <b>two three</b> four</p><p></p></div>",
            features,
            replacer=SoupReplacer(xformer=count_words),
        )
        assert [p["data-words"] for p in soup.find_all("p")] == ["4", "0"]

    @pytest.mark.parametrize("features", PARSERS)
    def test_xformer_can_remove_tags(self, features):
        # Removing a tag during parsing must not lose anything parsed
        # after it.
        def drop_empty_p(tag):
            if tag.name == "p" and not tag.get_text(strip=True):
                tag.decompose()

        soup = BeautifulSoup(
            "<div><p>keep</p><p> </p>after<p>last</p></div>",
            features,
            replacer=SoupReplacer(xformer=drop_empty_p),
        )
        assert [p.string for p in soup.find_all("p")] == ["keep", "last"]
        assert str(soup.div) == "<div><p>keep</p>after<p>last</p></div>"
        assert soup.div.get_text() == "keepafterlast"

    @pytest.mark.parametrize("features", PARSERS)
    def test_transformers_run_once_per_tag_in_order(self, features):
        # name_xformer and attrs_xformer both see the tag as parsed;
        # xformer runs after them and sees the result. Each tag is
        # transformed once, inner tags before the tags around them.
        seen = []

        def name_xformer(tag):
            return "strong" if tag.name == "b" else tag.name

        def attrs_xformer(tag):
            if tag.name == "b":
                return dict(tag.attrs, was="b")
            return tag.attrs

        def xformer(tag):
            seen.append((tag.name, tag.get("was")))

        soup = BeautifulSoup(
            "<p><b>x</b><i><b>y</b></i></p>",
            features,
            replacer=SoupReplacer(
                name_xformer=name_xformer,
                attrs_xformer=attrs_xformer,
                xformer=xformer,
            ),
        )
        # lxml's HTML parser adds <html> and <body>; they come last.
        assert seen[:4] == [
            ("strong", "b"),
            ("strong", "b"),
            ("i", None),
            ("p", None),
        ]
        assert [name for name, _ in seen[4:]] in ([], ["body", "html"])
        assert str(soup.p) == '<p><strong was="b">x</strong><i><strong was="b">y</strong></i></p>'
