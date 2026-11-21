from bs4 import BeautifulSoup, Tag
import argparse


parser = argparse.ArgumentParser(description="Print all tags by iterating over the soup")
parser.add_argument("input", help="path to input HTML or XML file")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as file:
    markup = file.read()

if args.input.lower().endswith(".xml"):
    parser_name = "xml"
else:
    parser_name = "html.parser"

soup = BeautifulSoup(markup, parser_name)

# Milestone 1 used soup.find_all(True), which builds a list of every tag
# first. Here the soup hands out one node at a time, and only the tags
# are printed (strings, comments, etc. are skipped).
for node in soup:
    if isinstance(node, Tag):
        print(node)
