from bs4 import BeautifulSoup, SoupReplacer
import argparse
from pathlib import Path


parser = argparse.ArgumentParser(description="set every paragraph class to test using SoupReplacer")
parser.add_argument("input", help="Path to the input HTML file")
parser.add_argument("--output", required=True, help="Path to the output file")
args = parser.parse_args()

if Path(args.input).resolve() == Path(args.output).resolve():
    parser.error("Input and output must be different files.")

with open(args.input, "r", encoding="utf-8") as file:
    html = file.read()

if args.input.lower().endswith(".xml"):
    parser_name = "xml"
else:
    parser_name = "html.parser"

# every <p> is built with class="test" while parsing, so there is no loop
p_class_test = SoupReplacer("p", "p", attrs={"class": "test"})

soup = BeautifulSoup(html, parser_name, replacer=p_class_test)

formatted_html = soup.prettify()

with open(args.output, "w", encoding="utf-8") as file:
    file.write(formatted_html)
