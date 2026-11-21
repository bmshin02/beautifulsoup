from bs4 import BeautifulSoup, Tag
import argparse


parser = argparse.ArgumentParser(description="Print every node of a document, one per line")
parser.add_argument("input", help="path to input HTML or XML file")
args = parser.parse_args()

with open(args.input, "r", encoding="utf-8") as file:
    markup = file.read()

if args.input.lower().endswith(".xml"):
    parser_name = "xml"
else:
    parser_name = "html.parser"

soup = BeautifulSoup(markup, parser_name)

# The example from the assignment: the soup itself is iterable.
# print(node) on a Tag would print its whole subtree, so each node is
# shown on one line as its type plus its name (Tags) or text (strings).
count = 0
for node in soup:
    count += 1
    if isinstance(node, Tag):
        print(f"{type(node).__name__}: <{node.name}>")
    else:
        print(f"{type(node).__name__}: {str(node)!r}")

print(f"{count} nodes")
