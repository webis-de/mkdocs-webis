<!-- markdownlint-disable MD041 -->

[![PyPi](https://img.shields.io/pypi/v/mkdocs-webis?style=flat-square)](https://pypi.org/project/mkdocs-webis/)
[![CI](https://img.shields.io/github/actions/workflow/status/webis-de/mkdocs-webis/ci.yml?branch=main&style=flat-square)](https://github.com/webis-de/mkdocs-webis/actions/workflows/ci.yml)
[![Code coverage](https://img.shields.io/codecov/c/github/webis-de/mkdocs-webis?style=flat-square)](https://codecov.io/github/webis-de/mkdocs-webis/)
[![Python](https://img.shields.io/pypi/pyversions/mkdocs-webis?style=flat-square)](https://pypi.org/project/mkdocs-webis/)
[![Issues](https://img.shields.io/github/issues/webis-de/mkdocs-webis?style=flat-square)](https://github.com/webis-de/mkdocs-webis/issues)
[![Commit activity](https://img.shields.io/github/commit-activity/m/webis-de/mkdocs-webis?style=flat-square)](https://github.com/webis-de/mkdocs-webis/commits)
[![Downloads](https://img.shields.io/pypi/dm/mkdocs-webis?style=flat-square)](https://pypi.org/project/mkdocs-webis/)
[![License](https://img.shields.io/github/license/webis-de/mkdocs-webis?style=flat-square)](LICENSE)

# 📘 mkdocs-webis

Webis style and BibTeX citations for [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

This MkDocs plugin...

- ... styles your documentation with the colors and rough design of the [Webis lecture notes](https://downloads.webis.de/lecturenotes/lecturenotes-generic/unit-en-lecturenotes-tutorial.pdf) (bold black titles, dark blue subtitles, square bullets, booktabs-like tables, and yellow highlight boxes), in a light and a dark color scheme,
- ... uses the system's Helvetica-like fonts instead of loading fonts from Google,
- ... lets you cite references from a BibTeX file with `[@key]`, and appends a list of the cited references (including their BibTeX) to each page.

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
  - webis:
      # Optional: BibTeX file in your docs directory.
      bibliography: references.bib
```

### Configuration

| Option | Default | Description |
| :-- | :-- | :-- |
| `style` | `true` | Add the Webis stylesheet. |
| `palette` | `true` | Use the Webis light (`webis`) and dark (`webis-dark`) color schemes, with a toggle. Set to `false` to configure `theme.palette` yourself. |
| `system_fonts` | `true` | Use the system's Helvetica-like fonts instead of Google Fonts. |
| `bibliography` | — | Path of a BibTeX file, relative to the docs directory. Enables citations. |
| `references_heading` | `References` | Heading of the references section appended to pages with citations. |
| `show_bibtex` | `true` | Show the BibTeX of each reference in a collapsible block. |

### Citations

With a `bibliography` configured, cite references by their BibTeX keys:

```markdown
Axioms are formal constraints on retrieval models [@fang2004formal].
Several studies use axioms to re-rank results [@hagen2016axiomatic; @bondarenko2022axiomatic].
```

Citations are rendered as author–year links (e.g., "(Fang et al., 2004)") to a "References" section at the bottom of the same page, which lists all references cited on that page.
Citations inside code are not replaced, and unknown keys fail the build.
The collapsible BibTeX blocks need the `admonition`, `pymdownx.details`, and `pymdownx.superfences` Markdown extensions.

We recommend copying BibTeX entries from [DBLP](https://dblp.org/).
All fields must be enclosed in braces (`title = {...}`), as in DBLP's export.

### Style Elements

Besides styling the standard Material elements, the stylesheet provides a few CSS classes:

```markdown
# Page Title

<p class="subtitle">A subtitle in dark blue, like on the slides.</p>

<span class="badge">TFC1</span> — a boxed label, e.g., for names or acronyms.

<div class="hero" markdown>
A highlighted introduction box, e.g., for the home page.
</div>
```

The color palette is available as CSS variables (e.g., `var(--webis-blue-ld)`, `var(--webis-red-tl1)`) for your own stylesheets.

## Development

To build this package and contribute to its development you need to install the `build`, `setuptools` and `wheel` packages:

```shell
pip install build setuptools wheel
```

(On most systems, these packages are already pre-installed.)

### Development installation

Install package and test dependencies:

```shell
pip install -e .[tests]
```

### Testing

Verify your changes against the test suite to verify.

```shell
ruff check .                   # Code format and LINT
mypy .                         # Static typing
bandit -c pyproject.toml -r .  # Security
pytest .                       # Unit tests
```

Please also add tests for your newly developed code.

### Build wheels

Wheels for this package can be built with:

```shell
python -m build
```

## Support

If you have any problems using this package, please file an [issue](https://github.com/webis-de/mkdocs-webis/issues/new).
We're happy to help!

## License

This repository is released under the [MIT license](LICENSE).
