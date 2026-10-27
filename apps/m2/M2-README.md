# Milestone-2

## Part 1: SoupStrainer

I redid tasks 2, 3, and 4 from Milestone 1 using SoupStrainer. I pass it to the constructor with parse_only, so BeautifulSoup only builds the tags that match. Everything else in the scripts is the same as Milestone 1.

To run (from the repository folder, Python 3.10, test-inputs/ is my Milestone 1 test files):

```bash
python apps/m2/task2.py test-inputs/python-index.html
python apps/m2/task3.py test-inputs/note.xml
python apps/m2/task4.py test-inputs/python-index.html
```

- **Task 2:** SoupStrainer("a") builds only the <a> tags, then find_all("a") prints them.
- **Task 3:** SoupStrainer(True) matches every tag, so it only skips what is outside all tags (in war-and-peace.html, the doctype and two line breaks: 3 of 43,747 nodes). The strainer can't help here because task 3 needs every tag.
- **Task 4:** SoupStrainer(id=True) builds only tags with an id. I still call find_all(id=True), because once a tag is kept, everything inside it is kept too, including children without an id.

All three print exactly the same output as Milestone 1 on all 10 of my test files.

### Large file test

war-and-peace.html (about 4 MB), best of 3 runs with /usr/bin/time -l, output sent to /dev/null:

| Task | Milestone 1 | Milestone 2 (SoupStrainer) |
|---|---|---|
| task 2 | 0.29 s, 67 MB | 0.19 s, 44 MB |
| task 3 | 0.59 s, 89 MB | 0.60 s, 89 MB |
| task 4 | 0.31 s, 67 MB | 0.19 s, 44 MB |

Tasks 2 and 4 were 35-40% faster and used about a third less memory. Task 3 did not change. The strainer still reads and parses the whole file; it only saves building tree objects for the parts I don't need.

## Part 2: Where the API functions are defined

Line numbers are from the original source code (the first commit in this repo).

| API | Defined at |
|---|---|
| `BeautifulSoup(...)` | `bs4/__init__.py:209` |
| `SoupStrainer(...)` | `bs4/filter.py:345` |
| `find_all()` | `bs4/element.py:2715` |
| `find()` | `bs4/element.py:2684` |
| `find_parent()` | `bs4/element.py:992` |
| `prettify()` | `bs4/element.py:2601` |
| `get_text()` | `bs4/element.py:524` |
| `tag["class"] = ...` | `bs4/element.py:2223` (`Tag.__setitem__`) |
| `tag.name = ...` | `bs4/element.py:1740` (plain attribute, no setter) |
| `print(tag)` | `bs4/element.py:2302` (`Tag.__str__`) |

## Part 3: SoupReplacer

SoupReplacer(og_tag, alt_tag) renames tags while the document is parsed, so there is no second pass over the tree:

```python
b_to_blockquote = SoupReplacer("b", "blockquote")
soup = BeautifulSoup(html_doc, "html.parser", replacer=b_to_blockquote)
```

What I changed (line numbers are after my changes):

| File | Change |
|---|---|
| `bs4/filter.py:685` | New `SoupReplacer` class. `replace(name)` returns `alt_tag` if `name` is `og_tag`, otherwise `name`. |
| `bs4/__init__.py:94`, `:36` | Import and export it, so `from bs4 import SoupReplacer` works. |
| `bs4/__init__.py:221`, `:447` | New `replacer=None` argument for the constructor, stored as `self.replacer`. I put it last so existing calls that pass arguments by position still work. |
| `bs4/__init__.py:1040` | In `handle_starttag`, the tag is created with the replaced name. This happens after the SoupStrainer check, so a strainer still matches the name in the file. |
| `bs4/__init__.py:1080` | In `handle_endtag`, the end tag is replaced too. Without this, `</b>` can't find the open `<blockquote>`, and everything after it ends up inside it. |
| `bs4/builder/_html5lib.py:126` | html5lib doesn't call `handle_starttag`, so it warns that replacer isn't supported, the same way it already does for `parse_only`. |

html.parser, lxml, and xml all go through `handle_starttag` and `handle_endtag`, so the change works for all three.

**Tests** (`bs4/tests/test_soupreplacer.py`), each run with html.parser, lxml, and xml:
1. `test_replaces_tags_during_parsing`: every `<b>` becomes a `<blockquote>` and keeps its attributes and text.
2. `test_end_tag_closes_replaced_tag`: in `<p><b>x</b>y</p>`, the `y` stays outside the blockquote.

```bash
pytest bs4/tests/test_soupreplacer.py
```

The full test suite has the same results as before my changes. 3 tests (`test_rejected_input` and 2 `test_rejected_markup`) already failed on the original code. They expect html.parser to reject some broken markup, and on Python 3.10.22 it doesn't.

**task6.py** does task 6 from Milestone 1 with SoupReplacer, so the loop that renamed each `<b>` is gone:

```bash
python apps/m2/task6.py test-inputs/war-and-peace.html --output war-and-peace-blockquote.html
```

The output files are exactly the same as Milestone 1 on all 10 of my test files. On war-and-peace.html it took about the same time (0.37 s vs 0.38 s), because the loop it removes is small next to parsing.
