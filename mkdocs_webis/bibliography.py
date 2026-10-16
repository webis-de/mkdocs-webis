"""
Citations from a BibTeX file.

- ``[@key]`` or ``[@key1; @key2]`` in a page is replaced by author–year links.
- Each page that cites at least one reference gets a references section at the
  bottom, listing the cited references, including the BibTeX of each entry.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from re import DOTALL, MULTILINE, Match, compile as re_compile
from typing import Final

_PATTERN_ENTRY: Final = re_compile(r"^@(\w+)\{([^,\s]+),", MULTILINE)
_PATTERN_FIELD_NAME: Final = re_compile(r"\s*(\w+)\s*=\s*\{")
_PATTERN_AUTHOR_SEPARATOR: Final = re_compile(r"\s+and\s+")
_PATTERN_CITATION: Final = re_compile(r"\[(@[\w-]+(?:\s*;\s*@[\w-]+)*)\]")
# Fenced code blocks and inline code spans, in which citations are not replaced.
_PATTERN_CODE: Final = re_compile(
    r"(^[ \t]*```.*?^[ \t]*```|`[^`\n]+`)", MULTILINE | DOTALL
)

_LATEX_REPLACEMENTS: Final[Mapping[str, str]] = {
    r"{\"{o}}": "ö",
    r"{\"{a}}": "ä",
    r"{\"{u}}": "ü",
    r"{\"{O}}": "Ö",
    r"{\"{A}}": "Ä",
    r"{\"{U}}": "Ü",
    r"{\'{e}}": "é",
    r"{\'{E}}": "É",
    r"{\'{o}}": "ó",
    r"{\'{a}}": "á",
    r"{\`{e}}": "è",
    r"{\u{a}}": "ă",
    r"{\^{a}}": "â",
    r"{\ss}": "ß",
    r"\&": "&",
    r"{-}": "-",
    r"\_": "_",
}


class BibliographyError(ValueError):
    """Raised for malformed BibTeX files or unknown citation keys."""


def _read_braced(text: str, start: int) -> int:
    """Return the index just after the brace closing the one opened before ``start``."""
    depth = 1
    index = start
    while depth > 0:
        if index >= len(text):
            raise BibliographyError("Unbalanced braces in BibTeX file.")
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
        index += 1
    return index


def clean_latex(value: str) -> str:
    """Convert (a subset of) LaTeX markup in a BibTeX value to plain text."""
    for latex, text in _LATEX_REPLACEMENTS.items():
        value = value.replace(latex, text)
    value = value.replace("{", "").replace("}", "")
    return " ".join(value.split())


@dataclass(frozen=True)
class Entry:
    """A BibTeX entry."""

    key: str
    entry_type: str
    fields: Mapping[str, str]
    bibtex: str

    @property
    def authors(self) -> list[str]:
        authors = self.fields.get("author") or self.fields.get("editor") or ""
        return [
            clean_latex(author)
            for author in _PATTERN_AUTHOR_SEPARATOR.split(authors)
            if author.strip()
        ]

    @property
    def year(self) -> str:
        return self.fields.get("year", "n.d.")

    @property
    def short_citation(self) -> str:
        """Author–year citation, e.g., "Fang et al., 2004"."""
        surnames = [author.split()[-1] for author in self.authors]
        if len(surnames) == 0:
            names = clean_latex(self.fields.get("title", self.key))
        elif len(surnames) == 1:
            names = surnames[0]
        elif len(surnames) == 2:
            names = f"{surnames[0]} and {surnames[1]}"
        else:
            names = f"{surnames[0]} et al."
        return f"{names}, {self.year}"

    @property
    def full_citation(self) -> str:
        """Full citation in Markdown."""
        authors = self.authors
        if len(authors) > 2:
            author_text = ", ".join(authors[:-1]) + ", and " + authors[-1]
        else:
            author_text = " and ".join(authors)
        title = clean_latex(self.fields.get("title", ""))
        venue = clean_latex(
            self.fields.get("booktitle")
            or self.fields.get("journal")
            or self.fields.get("institution")
            or self.fields.get("publisher")
            or self.fields.get("howpublished", "")
        )
        details = []
        if "volume" in self.fields and "journal" in self.fields:
            volume = self.fields["volume"]
            if "number" in self.fields:
                volume += f"({self.fields['number']})"
            details.append(volume)
        if "pages" in self.fields:
            details.append(clean_latex(self.fields["pages"]).replace("--", "–"))
        details.append(self.year)
        citation = f"{author_text}. **{title}.**"
        if venue:
            citation += f" _{venue}_,"
        citation += " " + ", ".join(details) + "."
        if "url" in self.fields:
            url = clean_latex(self.fields["url"])
            citation += f" [{url}]({url})"
        return citation

    @property
    def sort_key(self) -> tuple[str, str, str]:
        authors = self.authors
        first_author = authors[0].split()[-1].lower() if authors else ""
        return first_author, self.year, self.key


def parse_bibtex(text: str) -> dict[str, Entry]:
    """Parse the entries of a BibTeX file (fields must be enclosed in braces)."""
    entries: dict[str, Entry] = {}
    for match in _PATTERN_ENTRY.finditer(text):
        entry_type, key = match.groups()
        entry_end = _read_braced(text, match.start() + len(entry_type) + 2)
        fields: dict[str, str] = {}
        position = match.end()
        while (field_match := _PATTERN_FIELD_NAME.match(text, position)) is not None:
            value_end = _read_braced(text, field_match.end())
            fields[field_match.group(1).lower()] = text[
                field_match.end() : value_end - 1
            ]
            position = value_end + 1  # Skip the trailing comma.
        if key in entries:
            raise BibliographyError(f"Duplicate BibTeX key '{key}'.")
        entries[key] = Entry(
            key=key,
            entry_type=entry_type.lower(),
            fields=fields,
            bibtex=text[match.start() : entry_end],
        )
    return entries


@dataclass
class Bibliography:
    """Replace citations in Markdown pages and render reference lists."""

    entries: Mapping[str, Entry]
    heading: str = "References"
    show_bibtex: bool = True
    _cited_keys: set[str] = field(default_factory=set, init=False, repr=False)

    @classmethod
    def from_file(cls, path: Path, **kwargs) -> "Bibliography":
        return cls(entries=parse_bibtex(path.read_text(encoding="utf-8")), **kwargs)

    def _replace_citation(self, match: Match[str]) -> str:
        keys = [key.strip().lstrip("@") for key in match.group(1).split(";")]
        links = []
        for key in keys:
            if key not in self.entries:
                raise BibliographyError(f"Unknown citation key '{key}'.")
            self._cited_keys.add(key)
            links.append(f"[{self.entries[key].short_citation}](#{key})")
        return "(" + "; ".join(links) + ")"

    def render_references(self, keys: Iterable[str]) -> str:
        """Render the references section for the given keys."""
        entries = sorted((self.entries[key] for key in keys), key=lambda e: e.sort_key)
        blocks = [f"## {self.heading}\n"]
        for entry in entries:
            block = f'<a id="{entry.key}"></a>\n{entry.full_citation}\n'
            if self.show_bibtex:
                bibtex = "\n".join("    " + line for line in entry.bibtex.splitlines())
                block += f'\n??? quote "BibTeX"\n\n    ```bibtex\n{bibtex}\n    ```\n'
            blocks.append(block)
        return "\n".join(blocks)

    def process(self, markdown: str) -> str:
        """Replace citations and append the references section, if any."""
        self._cited_keys = set()
        # Odd indices of the split are code, which is kept as is.
        markdown = "".join(
            part
            if index % 2 == 1
            else _PATTERN_CITATION.sub(self._replace_citation, part)
            for index, part in enumerate(_PATTERN_CODE.split(markdown))
        )
        if self._cited_keys:
            markdown = (
                markdown.rstrip()
                + "\n\n"
                + self.render_references(self._cited_keys)
            )
        return markdown
