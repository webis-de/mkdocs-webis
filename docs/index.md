---
hide:
  - navigation
---

# mkdocs-webis

<p class="subtitle">Webis style and BibTeX citations for MkDocs Material.</p>

This documentation is rendered with the plugin itself, so it doubles as a demo of the style.

[Get started](#installation){ .md-button .md-button--primary }
[View on GitHub](https://github.com/webis-de/mkdocs-webis){ .md-button }
[View on PyPI](https://pypi.org/project/mkdocs-webis/){ .md-button }

This MkDocs plugin...

- ... styles your documentation like the [Webis homepage](https://webis.de/): a dark gray navigation bar with the Webis logo, the "Product Sans" and "Noto Sans" fonts, plain headings, blue links and buttons, flat tables, and a light gray footer,
- ... lets you cite references from a BibTeX file with `[@key]` or `[@key1, @key2]`, rendered as gray author–year citations like, and appends a list of the cited references (including their BibTeX) to each page.

## Installation

Install the package from [PyPI](https://pypi.org/project/mkdocs-webis/):

```shell
pip install mkdocs-webis
```

## Usage

Enable the plugin in your `mkdocs.yml` (together with the [Material](https://squidfunk.github.io/mkdocs-material/) theme):

```yaml
theme:
  name: material

plugins:
  - search
  - webis:
      bibliography: references.bib  # Optional: BibTeX file in your docs directory.
```

See the [style elements](style.md) for how Markdown elements look with this style.
