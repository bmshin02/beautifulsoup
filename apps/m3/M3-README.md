# Milestone-3

## The new SoupReplacer API

```python
SoupReplacer(og_tag, alt_tag)                                        # Milestone 2, still works
SoupReplacer(name_xformer=None, attrs_xformer=None, xformer=None)    # Milestone 3
```

Each transformer gets a `Tag`. `name_xformer` returns the new name, `attrs_xformer` returns the new attributes, and `xformer` changes the tag directly and returns nothing.

Each tag is transformed once, during parsing, when the parser closes it (inner tags first). `name_xformer` and `attrs_xformer` both see the tag as parsed, and `xformer` runs last. I picked closing time over opening time because:

- The parser closes tags by name. If `<b>` became `<blockquote>` when it opened, `</b>` wouldn't find it. After the end tag is matched, renaming is safe.
- At closing time the tag's children are all parsed, so `xformer` can look at them.

### Changes (line numbers are after my changes)

| File | Change |
|---|---|
| `bs4/filter.py:685` | `SoupReplacer` takes both forms. The Milestone-2 pair is turned into a `name_xformer` (`:751`), so there is one code path. `transform(tag)` is at `:771`. |
| `bs4/__init__.py:818` | `popTag` calls `replacer.transform(tag)`. The Milestone-2 code in `handle_starttag`/`handle_endtag` is removed. |
| `bs4/__init__.py:824` | Without this fix, an xformer that deleted its tag made everything after it disappear from the output. |

html5lib doesn't use `popTag`, so it still warns that replacer isn't supported.

## Tests

Six new tests in `bs4/tests/test_soupreplacer.py:63`, each run with html.parser, lxml, and xml: renaming with `name_xformer`, `attrs_xformer`, the `remove_class_attr` example, xformer seeing the finished tag, xformer deleting tags, and the order the three transformers run in.

```bash
pytest bs4/tests/test_soupreplacer.py
```

All 27 SoupReplacer tests pass (including Milestone 2's). The full suite has the same 3 failures as the original code.

## task7.py

Milestone-1 task 7 (every `<p>` gets `class="test"`) with `attrs_xformer`:

```bash
python apps/m3/task7.py test-inputs/python-index.html --output python-index-test-class.html
```

Output matches Milestone 1 exactly on all 10 of my test files. On war-and-peace.html, Milestones 1, 2, and 3 all take 0.40 s.

---

# Technical brief: SoupReplacer, Milestone 2 vs. Milestone 3

**Recommendation:** Ship the Milestone-3 transformer API as the only mechanism, and keep `SoupReplacer(og_tag, alt_tag)` as a shorthand built on it.

**Milestone 2 (a pair of names)** is easy to read, can't break anything, and can be inspected (`<SoupReplacer b -> blockquote>`). But every new use case needs a new parameter. Task 7 needed `attrs` right away, and "only `<b>` inside tables" would need another.

**Milestone 3 (functions)** handles any rule about a tag's name, attributes, or contents without changing BeautifulSoup again. The pair form can be written in terms of it, which is how I implemented it.

**Risks of the function API:**

1. **Timing must be documented.** Because tags are renamed at closing time, decisions the parser made while the tag was open use the old name (for example, `<br>` renamed to `<span>` prints as `<span/>`).
2. **User code runs inside the parser.** An xformer that deleted its tag broke the output until I fixed it. We should document that xformer may only change its own tag and that tag's contents.
3. **Functions can't be inspected** or saved like a pair can, and their errors happen in the middle of parsing.
4. **Cost:** a call per tag (14,899 on war-and-peace.html), but I measured no slowdown.

**Next steps:** document the timing and side-effect rules, keep the html5lib warning, and possibly allow a list of replacers so small transformers can be combined.
