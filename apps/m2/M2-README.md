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
