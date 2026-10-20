"""
Citations from a BibTeX file.

- ``[@key]`` or ``[@key1, @key2]`` in a page is replaced by author-year links,
  e.g., "[Fang et al., 2004]".
- Each page that cites at least one reference gets a references section at the
  bottom, listing the cited references, including the BibTeX of each entry.
- Citations that only appear in the rendered HTML (e.g., from docstrings
  inserted by mkdocstrings) are replaced as well, and their references are added.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from re import DOTALL, MULTILINE, Match, Pattern, compile as re_compile
from typing import Final

from bibtexparser.entrypoint import parse_string
from bibtexparser.middlewares import SeparateCoAuthors, SplitNameParts
from bibtexparser.middlewares.names import NameParts
from bibtexparser.model import DuplicateBlockKeyBlock, Entry as BibtexEntry
from pylatexenc.latex2text import LatexNodes2Text

_PATTERN_CITATION: Final = re_compile(r"\[(@[^\s,;\]]+(?:\s*[,;]\s*@[^\s,;\]]+)*)\]")
_PATTERN_CITATION_SEPARATOR: Final = re_compile(r"\s*[,;]\s*")
# Fenced code blocks and inline code spans, in which citations are not replaced.
_PATTERN_CODE: Final = re_compile(
    r"(^[ \t]*```.*?^[ \t]*```|`[^`\n]+`)", MULTILINE | DOTALL
)
# Code blocks and inline code in HTML, in which citations are not replaced.
_PATTERN_CODE_HTML: Final = re_compile(r"(<pre\b.*?</pre>|<code\b.*?</code>)", DOTALL)
# Fields that are not LaTeX (where, e.g., "%" is not a comment).
_VERBATIM_FIELDS: Final = frozenset({"url", "doi", "eprint"})

_latex_to_text: Final = LatexNodes2Text()


class BibliographyError(ValueError):
    """Raised for malformed BibTeX files or unknown citation keys."""


def clean_latex(value: str) -> str:
    """Convert LaTeX markup in a BibTeX value to plain text."""
    return " ".join(_latex_to_text.latex_to_text(value).split())


@dataclass(frozen=True)
class Author:
    """An author (or editor) name, split into its parts."""

    first: str
    last: str

    @property
    def full_name(self) -> str:
        return f"{self.first} {self.last}".strip()


def _author(name: NameParts) -> Author:
    return Author(
        first=clean_latex(" ".join(name.first)),
        last=clean_latex(" ".join([*name.von, *name.last, *name.jr])),
    )


@dataclass(frozen=True)
class Entry:
    """A BibTeX entry."""

    key: str
    entry_type: str
    fields: Mapping[str, str]
    authors: tuple[Author, ...]
    bibtex: str

    @classmethod
    def from_bibtex(cls, entry: BibtexEntry) -> "Entry":
        fields: dict[str, str] = {}
        names: list[NameParts] = []
        for bibtex_field in entry.fields:
            name = bibtex_field.key.lower()
            if name in ("author", "editor"):
                if name == "author" or not names:
                    names = bibtex_field.value
            elif name in _VERBATIM_FIELDS:
                fields[name] = bibtex_field.value
            else:
                fields[name] = clean_latex(bibtex_field.value)
        return cls(
            key=entry.key,
            entry_type=entry.entry_type.lower(),
            fields=fields,
            authors=tuple(_author(name) for name in names),
            bibtex=(entry.raw or "").strip(),
        )

    @property
    def year(self) -> str:
        return self.fields.get("year", "n.d.")

    @property
    def short_citation(self) -> str:
        """Author–year citation, e.g., "Fang et al., 2004"."""
        surnames = [author.last for author in self.authors]
        if len(surnames) == 0:
            names = self.fields.get("title", self.key)
        elif len(surnames) == 1:
            names = surnames[0]
        elif len(surnames) == 2:
            names = f"{surnames[0]} and {surnames[1]}"
        else:
            names = f"{surnames[0]} et al."
        return f"{names}, {self.year}"

    @property
    def link(self) -> str | None:
        """Link to the publication (its URL, or else its DOI)."""
        if "url" in self.fields:
            return self.fields["url"]
        if "doi" in self.fields:
            return f"https://doi.org/{self.fields['doi']}"
        return None

    @property
    def full_citation(self) -> str:
        """
        Full citation in HTML, like on webis.de, e.g., "Hui Fang, Tao Tao, and
        ChengXiang Zhai. A formal study of information retrieval heuristics.
        In SIGIR 2004, pages 49–56, 2004. ACM."
        """
        fields = {name: escape(value) for name, value in self.fields.items()}
        authors = [escape(author.full_name) for author in self.authors]
        if len(authors) > 2:
            author_text = ", ".join(authors[:-1]) + ", and " + authors[-1]
        else:
            author_text = " and ".join(authors)

        title = f'<span class="title">{fields.get("title", escape(self.key))}</span>'
        if self.link is not None:
            title = f'<a href="{escape(self.link)}">{title}</a>'

        details = []
        if "journal" in fields:
            journal = f'<span class="venue">{fields["journal"]}</span>'
            if "volume" in fields:
                journal += f", {fields['volume']}"
                if "number" in fields:
                    journal += f" ({fields['number']})"
                if "pages" in fields:
                    journal += f" : {fields['pages']}"
            elif "pages" in fields:
                journal += f", pages {fields['pages']}"
            details.append(journal)
        else:
            if "booktitle" in fields:
                details.append(f'In <span class="venue">{fields["booktitle"]}</span>')
            elif venue := (fields.get("institution") or fields.get("howpublished")):
                details.append(f'<span class="venue">{venue}</span>')
            if "pages" in fields:
                details.append(f"pages {fields['pages']}")
        details.append(escape(self.year))

        parts = [f"{author_text}." if author_text else "", f"{title}."]
        parts.append(", ".join(details) + ".")
        if "publisher" in fields and "journal" not in fields:
            parts.append(f"{fields['publisher']}.")
        return " ".join(part for part in parts if part)

    @property
    def sort_key(self) -> tuple[str, str, str]:
        first_author = self.authors[0].last.lower() if self.authors else ""
        return first_author, self.year, self.key


def parse_bibtex(text: str) -> dict[str, Entry]:
    """Parse the entries of a BibTeX file."""
    library = parse_string(
        text, append_middleware=[SeparateCoAuthors(), SplitNameParts()]
    )
    for block in library.failed_blocks:
        if isinstance(block, DuplicateBlockKeyBlock):
            raise BibliographyError(f"Duplicate BibTeX key '{block.key}'.")
        line = "" if block.start_line is None else f" (line {block.start_line + 1})"
        raise BibliographyError(f"Invalid BibTeX block{line}: {block.error}")
    return {entry.key: Entry.from_bibtex(entry) for entry in library.entries}


@dataclass
class Bibliography:
    """Replace citations in Markdown pages and render reference lists."""

    entries: Mapping[str, Entry]
    _cited_keys: set[str] = field(default_factory=set, init=False, repr=False)

    @classmethod
    def from_file(cls, path: Path) -> "Bibliography":
        return cls(entries=parse_bibtex(path.read_text(encoding="utf-8")))

    def _replace_citation(self, match: Match[str]) -> str:
        keys = [
            key.lstrip("@")
            for key in _PATTERN_CITATION_SEPARATOR.split(match.group(1))
        ]
        links = []
        for key in keys:
            if key not in self.entries:
                raise BibliographyError(f"Unknown citation key '{key}'.")
            self._cited_keys.add(key)
            citation = escape(self.entries[key].short_citation)
            links.append(f'<a href="#{escape(key)}">{citation}</a>')
        # Brackets as entities, so that they are not parsed as Markdown links.
        return '<span class="citation">&#91;' + "; ".join(links) + "&#93;</span>"

    def render_reference(self, entry: Entry) -> str:
        """Render a reference in HTML, with links to its BibTeX and DOI."""
        key = escape(entry.key)
        # A (visually hidden) checkbox toggles the BibTeX without JavaScript.
        toggle = (
            f'<input type="checkbox" id="bibtex-{key}" class="reference-toggle" '
            f'aria-label="Show BibTeX">'
        )
        links = [f'[<label for="bibtex-{key}">bib</label>]']
        bibtex = f'<pre class="reference-bibtex"><code>{escape(entry.bibtex)}</code></pre>'
        if "doi" in entry.fields:
            doi = escape(f"https://doi.org/{entry.fields['doi']}")
            links.append(f'[<a href="{doi}">doi</a>]')
        links_html = f'<span class="reference-links">{" ".join(links)}</span>'
        # No blank lines, so that Markdown keeps the block as raw HTML.
        block = [
            f'<div class="reference" id="{key}">',
            entry.full_citation,
            toggle + links_html,
            bibtex,
            "</div>",
        ]
        return "\n".join(block)

    def render_references(self, keys: Iterable[str]) -> str:
        """Render the references section for the given keys."""
        entries = sorted((self.entries[key] for key in keys), key=lambda e: e.sort_key)
        blocks = ["## References"]
        blocks.extend(self.render_reference(entry) for entry in entries)
        return "\n\n".join(blocks) + "\n"

    def _replace_citations(self, text: str, code_pattern: Pattern[str]) -> str:
        """Replace citations outside of code and remember the cited keys."""
        self._cited_keys = set()
        # Odd indices of the split are code, which is kept as is.
        return "".join(
            part
            if index % 2 == 1
            else _PATTERN_CITATION.sub(self._replace_citation, part)
            for index, part in enumerate(code_pattern.split(text))
        )

    def process(self, markdown: str) -> str:
        """Replace citations and append the references section, if any."""
        markdown = self._replace_citations(markdown, _PATTERN_CODE)
        if self._cited_keys:
            markdown = (
                markdown.rstrip()
                + "\n\n"
                + self.render_references(self._cited_keys)
            )
        return markdown

    def process_html(self, html: str) -> str:
        """
        Replace citations that remain in the rendered HTML of a page (e.g., from
        docstrings) and append their references, unless already listed.
        """
        html = self._replace_citations(html, _PATTERN_CODE_HTML)
        missing = [
            self.entries[key]
            for key in self._cited_keys
            if f'<div class="reference" id="{escape(key)}">' not in html
        ]
        if not missing:
            return html
        blocks = [html.rstrip()]
        if 'id="references"' not in html:
            blocks.append('<h2 id="references">References</h2>')
        blocks.extend(
            self.render_reference(entry)
            for entry in sorted(missing, key=lambda e: e.sort_key)
        )
        return "\n".join(blocks) + "\n"
