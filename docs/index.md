---
hide:
  - navigation
---

# mkdocs-webis

<p class="subtitle">Webis style and BibTeX citations for MkDocs Material.</p>

This documentation is rendered with the plugin itself, so it doubles as a demo of the style.

[Get started](#installation){ .md-button .md-button--primary }
[View on GitHub](https://github.com/webis-de/mkdocs-webis){ .md-button }

This MkDocs plugin...

- ... styles your documentation like the [Webis homepage](https://webis.de/): a dark gray navigation bar with the Webis logo, the "Product Sans" and "Noto Sans" fonts, plain headings, blue links and buttons, flat tables, and a light gray footer, in a light and a dark color scheme,
- ... lets you cite references from a BibTeX file with `[@key]` or `[@key1, @key2]`, rendered as gray author–year citations like [@fang2004formal], and appends a list of the cited references (including their BibTeX) to each page.

## Installation

Install the package from PyPI:

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

## Configuration

| Option | Default | Description |
|:--|:--|:--|
| `style` | `true` | Add the Webis stylesheet. |
| `palette` | `true` | Use the Webis light (`webis`) and dark (`webis-dark`) color schemes, with a toggle. Set to `false` to configure `theme.palette` yourself. |
| `header` | `true` | Show the navigation (with the `navigation.tabs` feature), the color scheme toggle, a repository icon, and a compact search in one header line, like on webis.de. |
| `google_fonts` | `false` | Load Noto Sans from Google Fonts. By default, like webis.de, only installed fonts are used ("Product Sans", "Noto Sans", or Verdana). |
| `logo` | `true` | Use the Webis logo and favicon, unless `theme.logo` or `theme.favicon` are set. |
| `bibliography` | — | Path of a BibTeX file, relative to the docs directory. Enables [citations](citations.md). |
| `references_heading` | `References` | Heading of the references section appended to pages with citations. |
| `show_bibtex` | `true` | Add a "[bib]" link to each reference that shows its BibTeX. |

See the [style elements](style.md) for how Markdown elements look with this style.
