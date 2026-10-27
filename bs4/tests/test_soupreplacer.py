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
