# Style Elements

<p class="subtitle">How Markdown and Material elements look in the Webis style.</p>

Use this page to check the style locally (`mkdocs serve`) when changing the stylesheet.

## Text

Regular text with **bold**, _italic_, `inline code`, [a link](https://webis.de/), and ==highlighted== text.
Keyboard keys look like <kbd>Ctrl</kbd> + <kbd>C</kbd>.

> A block quote, e.g., for a definition or a quotation.

### Third-Level Heading

#### Fourth-Level Heading

Term
:   A definition list entry.

## Lists

- An unordered list item
- Another item
    - A nested item
    - Another nested item

And an ordered list:

1. An ordered list item
2. Another item

## Tables

| Corpus | Publisher | Year | Documents |
|:--|:--|--:|--:|
| Webis-Query-Log | Webis | 2023 | 356,000,000 |
| ClueWeb22 | CMU | 2022 | 10,000,000,000 |
| MS MARCO | Microsoft | 2016 | 8,841,823 |

## Code

```python
from mkdocs_webis import parse_bibtex

# Parse a BibTeX file and print short citations.
entries = parse_bibtex(open("references.bib").read())
for key, entry in entries.items():
    print(f"{key}: {entry.short_citation}")
```

## Admonitions

!!! note
    A note, e.g., for additional information.

!!! tip
    A tip, e.g., for best practices.

!!! warning
    A warning, e.g., for common pitfalls.

!!! danger
    A danger notice, e.g., for destructive operations.

!!! example
    An example.

??? quote "A collapsible quote"
    Collapsed by default.

## Tabs

=== "pip"

    ```shell
    pip install mkdocs-webis
    ```

=== "uv"

    ```shell
    uv add mkdocs-webis
    ```

## Buttons, Badges, and Cards

[Primary button](#){ .md-button .md-button--primary }
[Default button](#){ .md-button }

<span class="badge">TFC1</span> — a small label, e.g., for names or acronyms.

<div class="grid cards" markdown>

- **Card one** — a short description.
- **Card two** — another short description.

</div>

## Custom Classes

The stylesheet provides a few CSS classes:

```markdown
<p class="subtitle">A gray subtitle below a page title.</p>

<span class="badge">TFC1</span> — a small label, e.g., for names or acronyms.
```

The colors of webis.de are available as CSS variables (e.g., `var(--webis-blue)`, `var(--webis-red)`) for your own stylesheets.
