from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from mkdocs.config import base, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

from mkdocs_webis.bibliography import Bibliography, BibliographyError
from mkdocs_webis.notebooks import NotebookConverter, NotebookFile, notebook_pages

_STYLESHEET_PATH = "assets/webis/webis.css"
_LOGO_PATH = "assets/webis/webis-logo.png"
_FAVICON_PATH = "assets/webis/favicon.png"
_DEFAULT_FAVICON_PATH = "assets/images/favicon.png"

# Only the light color scheme of webis.de, without a toggle.
_PALETTE = {"scheme": "webis", "primary": "custom", "accent": "custom"}

log = get_plugin_logger(__name__)


class WebisPluginConfig(base.Config):
    bibliography = config_options.Optional(config_options.Type(str))
    """Path of a BibTeX file (relative to the docs directory) for citations."""
    notebooks = config_options.Type(bool, default=False)
    """Render Jupyter notebooks (`.ipynb`) as pages."""


class WebisPlugin(BasePlugin[WebisPluginConfig]):
    """
    MkDocs plugin for the Webis style, BibTeX citations, and Jupyter notebooks.
    """

    _bibliography: Bibliography | None = None
    _notebook_converter: NotebookConverter | None = None
    _notebooks: list[File] = []
    _logo: bool = False
    _favicon: bool = False

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        theme = config.theme
        self._logo = False
        self._favicon = False
        if theme.name != "material":
            log.warning(
                f"The Webis style is designed for the Material theme, "
                f"but the theme is '{theme.name}'."
            )
        else:
            theme["palette"] = dict(_PALETTE)
            # The Webis header, after the user's custom_dir (which can override it).
            templates_dir = str(files("mkdocs_webis").joinpath("templates"))
            if templates_dir not in theme.dirs:
                index = 1 if theme.custom_dir else 0
                theme.dirs.insert(index, templates_dir)
            # Like webis.de, only use installed fonts (see the stylesheet).
            theme["font"] = False
            # The Webis logo and favicon, unless the theme configures its own.
            icon = theme.get("icon") or {}
            if not theme.get("logo") and not icon.get("logo"):
                theme["logo"] = _LOGO_PATH
                self._logo = True
            if theme.get("favicon") in (None, _DEFAULT_FAVICON_PATH):
                theme["favicon"] = _FAVICON_PATH
                self._favicon = True
        if _STYLESHEET_PATH not in config.extra_css:
            # Insert first, so that the user's stylesheets can override the style.
            config.extra_css.insert(0, _STYLESHEET_PATH)
        return config

    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        if self.config.notebooks and self._notebook_converter is None:
            self._notebook_converter = NotebookConverter()
        self._bibliography = None
        if self.config.bibliography is None:
            return
        path = Path(config.docs_dir) / self.config.bibliography
        if not path.is_file():
            raise PluginError(f"Bibliography file not found: {path}")
        try:
            self._bibliography = Bibliography.from_file(path)
        except BibliographyError as error:
            raise PluginError(f"Invalid bibliography file {path}: {error}") from error

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files | None:
        files.append(
            File.generated(
                config=config,
                src_uri=_STYLESHEET_PATH,
                content=files_resource("webis.css").read_text(encoding="utf-8"),
            )
        )
        if self._logo:
            files.append(
                File.generated(
                    config=config,
                    src_uri=_LOGO_PATH,
                    content=files_resource("webis-logo.png").read_bytes(),
                )
            )
        if self._favicon:
            files.append(
                File.generated(
                    config=config,
                    src_uri=_FAVICON_PATH,
                    content=files_resource("favicon.png").read_bytes(),
                )
            )
        self._notebooks = notebook_pages(files) if self.config.notebooks else []
        return files

    def on_page_read_source(self, /, *, page: Page, config: MkDocsConfig) -> str | None:
        if (
            self._notebook_converter is None
            or not isinstance(page.file, NotebookFile)
            or page.file.abs_src_path is None
        ):
            return None
        return self._notebook_converter.convert(page.file.abs_src_path)

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        # Copy the notebooks themselves, e.g., for downloading them.
        for notebook in self._notebooks:
            notebook.copy_file()

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        if self._bibliography is None:
            return markdown
        try:
            return self._bibliography.process(markdown)
        except BibliographyError as error:
            raise PluginError(f"{error} (in {page.file.src_uri})") from error

    def on_page_content(
        self, html: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        # Citations from content that other plugins insert while rendering the
        # Markdown (e.g., docstrings from mkdocstrings).
        if self._bibliography is None:
            return html
        try:
            return self._bibliography.process_html(html)
        except BibliographyError as error:
            raise PluginError(f"{error} (in {page.file.src_uri})") from error


def files_resource(name: str) -> Traversable:
    return files("mkdocs_webis").joinpath("assets", name)


__all__ = ["WebisPlugin", "WebisPluginConfig"]
