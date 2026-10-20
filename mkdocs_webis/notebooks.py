"""
Jupyter notebooks (`.ipynb`) as documentation pages.

Notebooks are converted to Markdown with nbconvert (see the `nbconvert/notebook.md.j2` template), so that MkDocs renders them like any other page.
"""

from base64 import b64encode
from importlib.resources import files
from typing import Any

from mkdocs.structure.files import File, Files
from nbconvert import MarkdownExporter
from nbformat import read
from traitlets.config import Config

from mkdocs_webis.widgets import WidgetRenderer, html_output

NOTEBOOK_SUFFIX = ".ipynb"


class NotebookFile(File):
    """
    A notebook rendered as a documentation page.
    """

    def is_documentation_page(self) -> bool:
        return True


def notebook_pages(files: Files) -> list[File]:
    """
    Replace the notebooks in the files by documentation pages and return the notebooks.
    """
    notebooks = [file for file in files if file.src_uri.endswith(NOTEBOOK_SUFFIX)]
    for notebook in notebooks:
        files.remove(notebook)
        files.append(
            NotebookFile(
                notebook.src_uri,
                notebook.src_dir,
                notebook.dest_dir,
                notebook.use_directory_urls,
                inclusion=notebook.inclusion,
            )
        )
    return notebooks


def _base64(text: str) -> str:
    return b64encode(text.encode()).decode()


def _widget(view: dict[str, Any], metadata: dict[str, Any]) -> str:
    return WidgetRenderer(metadata).render_view(view)


class NotebookConverter:
    """
    Convert notebooks to Markdown with nbconvert.
    """

    def __init__(self) -> None:
        self._exporter = MarkdownExporter(
            config=Config(
                # Embed images instead of extracting them to separate files.
                ExtractOutputPreprocessor={"enabled": False},
            ),
            template_file="notebook.md.j2",
            extra_template_paths=[str(files("mkdocs_webis").joinpath("nbconvert"))],
            filters={"base64": _base64, "html_output": html_output, "widget": _widget},
        )

    def convert(self, path: str) -> str:
        markdown, _ = self._exporter.from_notebook_node(read(path, as_version=4))
        return markdown
