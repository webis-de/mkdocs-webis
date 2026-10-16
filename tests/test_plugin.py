from pathlib import Path

from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort, PluginError
from pytest import raises

BIBTEX = """@article{doe2020test,
  author       = {Jane Doe},
  title        = {A Test},
  journal      = {Journal of Tests},
  year         = {2020}
}
"""


def _build(
    tmp_path: Path,
    plugin_config: str,
    page: str = "# Home\n",
    theme: str = "",
    extra_config: str = "",
) -> Path:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text(page)
    (docs_dir / "references.bib").write_text(BIBTEX)
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        "site_name: Test\n"
        f"{extra_config}"
        "theme:\n"
        "  name: material\n"
        f"{theme}"
        "plugins:\n"
        f"  - webis{plugin_config}\n"
    )
    site_dir = tmp_path / "site"
    config = load_config(str(config_file), site_dir=str(site_dir))
    build(config)
    return site_dir


def test_style_and_palette(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, "")
    assert (site_dir / "assets" / "webis" / "webis.css").is_file()
    html = (site_dir / "index.html").read_text()
    assert "assets/webis/webis.css" in html
    assert 'data-md-color-scheme="webis"' in html
    assert "fonts.googleapis.com" not in html
    assert (site_dir / "assets" / "webis" / "webis-logo.png").is_file()
    assert "assets/webis/webis-logo.png" in html
    assert "assets/webis/favicon.png" in html


def test_header(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path,
        "",
        theme="  features:\n    - navigation.tabs\n",
        extra_config="repo_url: https://github.com/webis-de/mkdocs-webis\n",
    )
    html = (site_dir / "index.html").read_text()
    assert 'class="md-header md-header--shadow webis-header"' in html
    assert 'class="webis-header__nav-link"' in html
    assert 'class="md-tabs"' not in html
    # Order: navigation, palette toggle, repository icon (then search, if enabled).
    positions = [
        html.index("webis-header__nav"),
        html.index('data-md-component="palette"'),
        html.index("webis-header__source"),
    ]
    assert positions == sorted(positions)


def test_no_header(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path,
        ":\n      header: false",
        theme="  features:\n    - navigation.tabs\n",
    )
    html = (site_dir / "index.html").read_text()
    assert "webis-header" not in html
    assert 'class="md-tabs"' in html


def test_google_fonts(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, ":\n      google_fonts: true")
    html = (site_dir / "index.html").read_text()
    assert "fonts.googleapis.com" in html
    assert "Noto+Sans" in html


def test_own_logo(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, "", theme="  logo: logo.svg\n  favicon: logo.svg\n")
    assert not (site_dir / "assets" / "webis" / "webis-logo.png").exists()
    assert not (site_dir / "assets" / "webis" / "favicon.png").exists()
    html = (site_dir / "index.html").read_text()
    assert "logo.svg" in html


def test_no_style(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path, ":\n      style: false\n      palette: false\n      logo: false"
    )
    assert not (site_dir / "assets" / "webis" / "webis.css").exists()
    assert not (site_dir / "assets" / "webis" / "webis-logo.png").exists()
    html = (site_dir / "index.html").read_text()
    assert 'data-md-color-scheme="webis"' not in html


def test_citations(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path,
        ":\n      bibliography: references.bib",
        page="# Home\n\nAs shown before [@doe2020test].\n",
    )
    html = (site_dir / "index.html").read_text()
    assert 'class="citation"' in html
    assert '&#91;<a href="#doe2020test">Doe, 2020</a>&#93;' in html
    assert 'id="references"' in html
    assert '<div class="reference" id="doe2020test">' in html
    assert '<label for="bibtex-doe2020test">bib</label>' in html
    assert '<pre class="reference-bibtex"><code>@article{doe2020test,' in html


def test_unknown_citation(tmp_path: Path) -> None:
    with raises((PluginError, Abort)):
        _build(
            tmp_path,
            ":\n      bibliography: references.bib",
            page="# Home\n\nAs shown before [@unknown].\n",
        )


def test_missing_bibliography(tmp_path: Path) -> None:
    with raises((PluginError, Abort)):
        _build(tmp_path, ":\n      bibliography: missing.bib")
