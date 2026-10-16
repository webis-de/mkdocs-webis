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

- ... styles your documentation like the [Webis homepage](https://webis.de/) (a dark gray navigation bar with the Webis logo, the "Product Sans" and "Noto Sans" fonts, plain headings, blue links and buttons, flat tables, and a light gray footer),
- ... lets you cite references from a BibTeX file with `[@key]` or `[@key1, @key2]`, rendered as gray author–year citations like "[Fang et al., 2004]", and appends a list of the cited references (including their BibTeX) to each page.

The [documentation](https://webis-de.github.io/mkdocs-webis/) is rendered with the plugin itself, so it doubles as a demo.

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
| `header` | `true` | Show the navigation (with the `navigation.tabs` feature), a repository icon, and a compact search in one header line, like on webis.de. |
| `google_fonts` | `false` | Load Noto Sans from Google Fonts. By default, like webis.de, only installed fonts are used ("Product Sans", "Noto Sans", or Verdana). |
| `logo` | `true` | Use the Webis logo and favicon, unless `theme.logo` or `theme.favicon` are set. |
| `bibliography` | — | Path of a BibTeX file, relative to the docs directory. Enables citations. |
| `references_heading` | `References` | Heading of the references section appended to pages with citations. |
| `show_bibtex` | `true` | Add a "[bib]" link to each reference that shows its BibTeX. |

### Citations

With a `bibliography` configured, cite references by their BibTeX keys:

```markdown
Axioms are formal constraints on retrieval models [@fang2004formal].
Some studies use axioms for re-ranking [@hagen2016axiomatic, @bondarenko2022axiomatic].
```

Citations are rendered as gray author–year links in brackets (e.g., "[Fang et al., 2004]" or "[Hagen et al., 2016; Bondarenko et al., 2022]"), like on the Webis slides.
They link to a "References" section at the bottom of the same page, which lists all references cited on that page.
Multiple keys are separated by commas or semicolons.

We recommend copying BibTeX entries from [DBLP](https://dblp.org/).

### Style Elements

Besides styling the standard Material elements, the stylesheet provides a few CSS classes:

```markdown
# Page Title

<p class="subtitle">A gray subtitle below the page title.</p>

<span class="badge">TFC1</span> — a small label, e.g., for names or acronyms.
```

The colors of webis.de are available as CSS variables (e.g., `var(--webis-blue)`, `var(--webis-red)`) for your own stylesheets.
See the [style elements](https://webis-de.github.io/mkdocs-webis/style/) for how all elements look.

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
ruff check .  # Code format, LINT, and security
mypy .        # Static typing
pytest .      # Unit tests
```

Please also add tests for your newly developed code.

### Documentation and demo

The documentation in [`docs/`](docs/) uses the plugin itself, including a [page with all style elements](docs/style.md) and [citations](docs/citations.md).
Preview it locally to check changes to the style or the citations:

```shell
mkdocs serve
```

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
