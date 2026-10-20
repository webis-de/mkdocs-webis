from pathlib import Path

from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort, PluginError
from nbformat import writes
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output
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
    files: dict[str, str] | None = None,
) -> Path:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text(page)
    (docs_dir / "references.bib").write_text(BIBTEX)
    for name, content in (files or {}).items():
        (docs_dir / name).write_text(content)
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


def test_style_and_scheme(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, "")
    assert (site_dir / "assets" / "webis" / "webis.css").is_file()
    html = (site_dir / "index.html").read_text()
    assert "assets/webis/webis.css" in html
    assert 'data-md-color-scheme="webis"' in html
    # Light mode only, without a toggle.
    assert 'data-md-component="palette"' not in html
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
    # Order: navigation, then repository icon (then search, if enabled).
    assert html.index("webis-header__nav") < html.index("webis-header__source")


def test_custom_dir_overrides_header(tmp_path: Path) -> None:
    custom_dir = tmp_path / "overrides" / "partials"
    custom_dir.mkdir(parents=True)
    (custom_dir / "header.html").write_text("<header>Custom header</header>")
    site_dir = _build(tmp_path, "", theme="  custom_dir: overrides\n")
    html = (site_dir / "index.html").read_text()
    assert "Custom header" in html
    assert "webis-header" not in html


def test_own_logo(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, "", theme="  logo: logo.svg\n  favicon: logo.svg\n")
    assert not (site_dir / "assets" / "webis" / "webis-logo.png").exists()
    assert not (site_dir / "assets" / "webis" / "favicon.png").exists()
    html = (site_dir / "index.html").read_text()
    assert "logo.svg" in html


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


def test_citations_in_rendered_html(tmp_path: Path) -> None:
    # Simulate content inserted while rendering the Markdown (e.g., docstrings).
    (tmp_path / "hooks.py").write_text(
        "def on_page_markdown(markdown, **kwargs):\n"
        "    return markdown.replace('DOCSTRING', '<p>[@doe2020test]</p>')\n"
    )
    site_dir = _build(
        tmp_path,
        ":\n      bibliography: references.bib",
        page="# Home\n\nDOCSTRING\n",
        extra_config="hooks:\n  - hooks.py\n",
    )
    html = (site_dir / "index.html").read_text()
    assert "[@doe2020test]" not in html
    assert '&#91;<a href="#doe2020test">Doe, 2020</a>&#93;' in html
    assert '<h2 id="references">References</h2>' in html
    assert '<div class="reference" id="doe2020test">' in html


def _notebook() -> str:
    return writes(
        new_notebook(
            cells=[
                new_markdown_cell("# Notebook\n\nAs shown before [@doe2020test]."),
                new_code_cell(
                    "print('hello')\nframe",
                    outputs=[
                        new_output("stream", name="stdout", text="hello\n"),
                        new_output("stream", name="stderr", text="Some warning\n"),
                        new_output(
                            "display_data",
                            data={
                                "application/vnd.jupyter.widget-view+json": {},
                                "text/plain": "Progress: 100%",
                            },
                        ),
                        new_output(
                            "execute_result",
                            data={
                                "text/html": "<div>\n<style scoped>\n"
                                ".dataframe tbody tr th {}\n</style>\n"
                                '<table border="1" class="dataframe">'
                                "<tr><td>1</td></tr></table>\n</div>",
                                "text/plain": "   a\n0  1",
                            },
                            execution_count=1,
                        ),
                        new_output(
                            "display_data",
                            data={"image/svg+xml": "<svg></svg>"},
                        ),
                    ],
                    execution_count=1,
                ),
                new_code_cell(
                    "1 / 0",
                    outputs=[
                        new_output(
                            "error",
                            ename="ZeroDivisionError",
                            evalue="division by zero",
                            traceback=[
                                "\x1b[31mZeroDivisionError\x1b[0m: division by zero"
                            ],
                        ),
                    ],
                    execution_count=2,
                ),
                new_code_cell("1 + 1", outputs=[]),
            ],
            metadata={"language_info": {"name": "python"}},
        )
    )


def test_notebooks(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path,
        ":\n      bibliography: references.bib\n      notebooks: true",
        extra_config=(
            "markdown_extensions:\n  - pymdownx.highlight\n  - pymdownx.superfences\n"
        ),
        files={"notebook.ipynb": _notebook()},
    )
    html = (site_dir / "notebook" / "index.html").read_text()
    # Markdown cells are rendered like other pages (e.g., with citations).
    assert '<h1 id="notebook">Notebook</h1>' in html
    assert '&#91;<a href="#doe2020test">Doe, 2020</a>&#93;' in html
    # Code cells and text outputs are code blocks, with prompts like in Jupyter.
    assert '<span class="nb">print</span>' in html
    assert "<code>hello\n</code>" in html
    assert '<div class="jupyter-prompt jupyter-prompt--input">In [1]:</div>' in html
    assert '<div class="jupyter-prompt jupyter-prompt--input">In [ ]:</div>' in html
    assert '<div class="jupyter-prompt jupyter-prompt--output">Out[1]:</div>' in html
    # Errors show the traceback (without colors).
    assert "<code>ZeroDivisionError: division by zero\n</code>" in html
    # Vector graphics are embedded.
    assert 'src="data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="' in html
    # Data frames use the theme's table style.
    assert "<table><tr><td>1</td></tr></table>" in html
    assert "<style scoped>" not in html
    # Logs and widgets are skipped.
    assert "Some warning" not in html
    assert "Progress: 100%" not in html
    # The notebook itself can be downloaded.
    assert (site_dir / "notebook.ipynb").is_file()
    assert 'href="../notebook.ipynb" title="Download notebook"' in html


def test_notebooks_disabled(tmp_path: Path) -> None:
    site_dir = _build(tmp_path, "", files={"notebook.ipynb": _notebook()})
    assert not (site_dir / "notebook" / "index.html").exists()
    assert (site_dir / "notebook.ipynb").is_file()


def _widget_notebook() -> str:
    def model(name: str, **state: object) -> dict[str, object]:
        return {"model_name": f"{name}Model", "state": state}

    def view(model_id: str) -> dict[str, object]:
        return {
            "application/vnd.jupyter.widget-view+json": {"model_id": model_id},
            "text/plain": f"Widget {model_id}",
        }

    return writes(
        new_notebook(
            cells=[
                new_code_cell(
                    "IntSlider()",
                    outputs=[
                        new_output(
                            "execute_result", data=view("box"), execution_count=1
                        ),
                        new_output("display_data", data=view("unknown")),
                    ],
                    execution_count=1,
                ),
            ],
            metadata={
                "widgets": {
                    "application/vnd.jupyter.widget-state+json": {
                        "state": {
                            "box": model(
                                "HBox",
                                children=["IPY_MODEL_slider", "IPY_MODEL_output"],
                            ),
                            "slider": model(
                                "IntSlider", description="<k>", min=1, max=9, value=3
                            ),
                            "output": model(
                                "Output",
                                outputs=[
                                    {
                                        "output_type": "stream",
                                        "name": "stdout",
                                        "text": "k is 3\n",
                                    }
                                ],
                            ),
                        },
                    },
                },
            },
        )
    )


def test_notebook_widgets(tmp_path: Path) -> None:
    site_dir = _build(
        tmp_path,
        ":\n      notebooks: true",
        files={"notebook.ipynb": _widget_notebook()},
    )
    html = (site_dir / "notebook" / "index.html").read_text()
    # Widgets are shown disabled, as saved in the widget state.
    assert '<div class="jupyter-prompt jupyter-prompt--output">Out[1]:</div>' in html
    assert '<span class="jupyter-widget__description">&lt;k&gt;</span>' in html
    assert '<input type="range" min="1" max="9" step="any" value="3" disabled>' in html
    assert '<span class="jupyter-widget__readout">3</span>' in html
    assert "<pre><code>k is 3</code></pre>" in html
    # Widgets without saved state are skipped.
    assert "Widget" not in html
