# Milestone-4

## Iterable BeautifulSoup

```python
soup = BeautifulSoup(html_doc, "html.parser")
for node in soup:
    print(node)
```

`soup` is still the regular object the `BeautifulSoup` constructor returns. Looping over it now visits every node in the document, one at a time, in document order (depth-first, each tag before its children). A node is anything in the tree: `Tag`, `NavigableString`, `Comment`, `Doctype`, `CData`, `ProcessingInstruction`, and so on. The soup itself isn't a node of the document, so it isn't yielded.

### How it works

`BeautifulSoup.__iter__` (`bs4/__init__.py:691`) is a generator:

```python
def __iter__(self):
    node = self.contents[0] if self.contents else None
    while node is not None:
        successor = node.next_element
        yield node
        node = successor
```

While parsing, BeautifulSoup already links every node to the node parsed right after it (`next_element`). That chain is the document in depth-first order. So the generator only has to start at the first child and follow the links until they run out. It holds one node at a time: no list of nodes, no stack, and no recursion. Each `next()` call does a constant amount of work.

The next node is looked up *before* the current one is handed to the loop body. So the loop body can change the node it was given (rename it, edit its attributes, or replace a string) without breaking the iteration.

### Changes (line numbers are after my changes)

| File | Change |
|---|---|
| `bs4/__init__.py:691` | New `BeautifulSoup.__iter__`, the generator above. |

Nothing else changed. `Tag.__iter__` (`bs4/element.py:2208`) still gives a tag's direct children, so `for child in soup.body` works the same as before. I checked every parser (html.parser, lxml, lxml-xml, html5lib), and in all of them the chain from the first child ends at `None` after the last node. That's why the loop doesn't need a stop node.

## Tests

Five new tests in `bs4/tests/test_soupiterator.py:28`, one for each kind of object:

| Test | What it checks |
|---|---|
| `test_yields_tags_in_document_order` (`:29`) | Nested tags come out depth-first, each before its children. The soup isn't yielded. `for child in tag` still gives direct children. |
| `test_yields_text_nodes` (`:47`) | Text between tags, text inside nested tags, and whitespace-only text each come out once, in the right place among the tags. |
| `test_yields_special_strings` (`:63`) | `Doctype`, `Comment`, `CData`, and `ProcessingInstruction` nodes come out with their own classes. |
| `test_yields_xml_nodes` (`:80`) | An XML document with an `XMLProcessingInstruction`, namespaced tags (`dc:creator`), an empty-element tag, and a comment. |
| `test_iteration_is_lazy` (`:104`) | `iter(soup)` is a generator, and `next()` gives one node. A tag added *after* iteration started is still visited, which couldn't happen if the nodes had been copied into a list first. With all four parsers, the result matches `Tag.descendants`. |

```bash
pytest bs4/tests/test_soupiterator.py
```

All 8 runs pass (the last test runs once per parser). The full suite has the same 3 failures as the original code (`test_rejected_input` and two `test_rejected_markup` cases, caused by the newer Python html.parser).

## Apps

`apps/m4/iterate.py` is the example from the assignment. It prints every node, one per line, and then the node count:

```bash
python apps/m4/iterate.py test-inputs/note.xml
```

```
Tag: <note>
NavigableString: '\n'
Tag: <to>
NavigableString: 'Tove'
...
14 nodes
```

`apps/m4/task3.py` is Milestone-1 task 3 (print every tag). Milestone 1 used `soup.find_all(True)`, which builds a list of every tag first. This version loops over the soup and prints the nodes that are tags:

```bash
python apps/m4/task3.py test-inputs/war-and-peace.html
```

Its output is identical to Milestone 1's on all 10 of my test files.

---

# Technical brief: iterable BeautifulSoup

**Recommendation:** Ship `for node in soup` as a generator that follows the `next_element` chain. Keep `for child in tag` as it is.

### Why a generator and not a list

On war-and-peace.html (43,747 nodes), measured after parsing:

| Approach | Extra memory | Time per pass |
|---|---|---|
| `for node in soup` (generator) | 1.1 KiB | 1.7 ms |
| `list(soup.descendants)` | 344.5 KiB | 2.0 ms |

The generator's memory stays the same however big the document is. A list grows with the number of nodes, and the first node isn't available until the whole list is built. With a generator, the caller gets the first node right away. The caller can also stop early (`break`) or chain the stream into other generators. This is the *Lazy Rivers* style (EPS Ch. 28): data comes to the caller as a stream, pulled one item at a time, instead of all at once.

### Other options I considered

1. **Depth-first search with a stack** of child iterators: O(depth) memory. It works, but the tree already stores its own traversal order in `next_element`, so the stack would duplicate it.
2. **Recursive generator** (`yield from` per child): the shortest code, but a deeply nested document can hit Python's recursion limit. I tried 3,000 nested `<div>` tags: the recursive version raised `RecursionError`, and the `next_element` generator visited all 3,001 nodes.
3. **Changing `Tag.__iter__`** so that every tag iterates its descendants: this would change what `for x in tag` and `list(tag)` mean for all existing bs4 code. Only the soup needed to change.

### Risks

1. **Two meanings of iteration.** `for x in soup` visits every node, but `for x in soup.body` visits only direct children, and `len(soup)` still counts only top-level children. This needs to be documented.
2. **Removing the current tag inside the loop.** Changing the current node, or replacing a string, is safe. But if the loop body extracts or decomposes the *current tag*, the loop walks that tag's detached children and then stops, so the rest of the document is skipped. This is the same rule as modifying a Python list while looping over it. To delete tags, collect them first (for example with `find_all`) or delete them with `SoupReplacer` while parsing.
3. **Nodes added during iteration.** Because nothing is collected ahead of time, nodes added later in the document are visited. This is the expected behavior for a lazy stream, but a loop that keeps inserting nodes ahead of itself would never end.

**Next steps:** document the two meanings of iteration and the removal rule. A safe-removal mode could be added later: remember the node before the current one, and resume from it if the current tag was removed.
