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


def _build(tmp_path: Path, plugin_config: str, page: str = "# Home\n") -> Path:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text(page)
    (docs_dir / "references.bib").write_text(BIBTEX)
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        "site_name: Test\n"
        "theme:\n"
        "  name: material\n"
        "markdown_extensions:\n"
        "  - admonition\n"
        "  - pymdownx.details\n"
        "  - pymdownx.superfences\n"
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


def test_no_style(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, ":\n      style: false\n      palette: false")
    assert not (site_dir / "assets" / "webis" / "webis.css").exists()
    html = (site_dir / "index.html").read_text()
    assert 'data-md-color-scheme="webis"' not in html


def test_citations(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path,
        ":\n      bibliography: references.bib",
        page="# Home\n\nAs shown before [@doe2020test].\n",
    )
    html = (site_dir / "index.html").read_text()
    assert 'href="#doe2020test"' in html
    assert "Doe, 2020" in html
    assert 'id="references"' in html
    assert 'id="doe2020test"' in html


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
