from bs4 import BeautifulSoup, SoupStrainer
import argparse

parser = argparse.ArgumentParser(description="Print the tags with an id using SoupStrainer")
parser.add_argument("input", help="path to input HTML or XML file")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as file:
    markup = file.read()

if args.input.lower().endswith(".xml"):
    parser_name = "xml"
else:
    parser_name = "html.parser"

# only build tags that have an id attribute (and what is inside them)
has_id = SoupStrainer(id=True)

soup = BeautifulSoup(markup, parser_name, parse_only=has_id)


# a kept tag can have children without an id, so filter again
tags = soup.find_all(id=True)

for tag in tags:
    print(tag)
