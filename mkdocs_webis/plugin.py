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

_STYLESHEET_PATH = "assets/webis/webis.css"
_LOGO_PATH = "assets/webis/webis-logo.png"
_FAVICON_PATH = "assets/webis/favicon.png"
_DEFAULT_FAVICON_PATH = "assets/images/favicon.png"
_GOOGLE_FONTS = {"text": "Noto Sans", "code": "Noto Sans Mono"}

_PALETTE = [
    {
        "media": "(prefers-color-scheme: light)",
        "scheme": "webis",
        "primary": "custom",
        "accent": "custom",
        "toggle": {"icon": "material/weather-night", "name": "Switch to dark mode"},
    },
    {
        "media": "(prefers-color-scheme: dark)",
        "scheme": "webis-dark",
        "primary": "custom",
        "accent": "custom",
        "toggle": {"icon": "material/weather-sunny", "name": "Switch to light mode"},
    },
]

log = get_plugin_logger(__name__)


class WebisPluginConfig(base.Config):
    style = config_options.Type(bool, default=True)
    """Add the Webis stylesheet."""
    palette = config_options.Type(bool, default=True)
    """Use the Webis light and dark color schemes for the Material theme."""
    google_fonts = config_options.Type(bool, default=False)
    """Load Noto Sans from Google Fonts (otherwise, only use installed fonts)."""
    logo = config_options.Type(bool, default=True)
    """Use the Webis logo and favicon, unless the theme configures its own."""
    bibliography = config_options.Optional(config_options.Type(str))
    """Path of a BibTeX file (relative to the docs directory) for citations."""
    references_heading = config_options.Type(str, default="References")
    """Heading of the references section appended to pages with citations."""
    show_bibtex = config_options.Type(bool, default=True)
    """Show the BibTeX of each reference in a collapsible block."""


class WebisPlugin(BasePlugin[WebisPluginConfig]):
    """
    MkDocs plugin for the Webis style and BibTeX citations.
    """

    _bibliography: Bibliography | None = None
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
            if self.config.palette:
                theme["palette"] = _PALETTE
            # Like webis.de, prefer Product Sans and Noto Sans (see the stylesheet).
            theme["font"] = dict(_GOOGLE_FONTS) if self.config.google_fonts else False
            if self.config.logo:
                icon = theme.get("icon") or {}
                if not theme.get("logo") and not icon.get("logo"):
                    theme["logo"] = _LOGO_PATH
                    self._logo = True
                if theme.get("favicon") in (None, _DEFAULT_FAVICON_PATH):
                    theme["favicon"] = _FAVICON_PATH
                    self._favicon = True
        if self.config.style and _STYLESHEET_PATH not in config.extra_css:
            # Insert first, so that the user's stylesheets can override the style.
            config.extra_css.insert(0, _STYLESHEET_PATH)
        return config

    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        self._bibliography = None
        if self.config.bibliography is None:
            return
        path = Path(config.docs_dir) / self.config.bibliography
        if not path.is_file():
            raise PluginError(f"Bibliography file not found: {path}")
        try:
            self._bibliography = Bibliography.from_file(
                path,
                heading=self.config.references_heading,
                show_bibtex=self.config.show_bibtex,
            )
        except BibliographyError as error:
            raise PluginError(f"Invalid bibliography file {path}: {error}") from error

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files | None:
        if self.config.style:
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
        return files

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        if self._bibliography is None:
            return markdown
        try:
            return self._bibliography.process(markdown)
        except BibliographyError as error:
            raise PluginError(f"{error} (in {page.file.src_uri})") from error


def files_resource(name: str) -> Traversable:
    return files("mkdocs_webis").joinpath("assets", name)


__all__ = ["WebisPlugin", "WebisPluginConfig"]
