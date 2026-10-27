from bs4 import BeautifulSoup, SoupStrainer
import argparse

parser = argparse.ArgumentParser(description="Print anchor tags using SoupStrainer")
parser.add_argument("input", help="path to input HTML or XML file")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as file:
    markup = file.read()

if args.input.lower().endswith(".xml"):
    parser_name = "xml"
else:
    parser_name = "html.parser"

# only build <a> tags (and what is inside them) into the tree
only_links = SoupStrainer("a")

soup = BeautifulSoup(markup, parser_name, parse_only=only_links)


links = soup.find_all("a")

for link in links:
    print(link)
