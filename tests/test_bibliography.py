from pytest import raises

from mkdocs_webis.bibliography import Bibliography, BibliographyError, parse_bibtex

BIBTEX = r"""
% A comment.
@inproceedings{fang2004formal,
  author       = {Hui Fang and
                  Tao Tao and
                  ChengXiang Zhai},
  title        = {A formal study of information retrieval heuristics},
  booktitle    = {{SIGIR} 2004},
  pages        = {49--56},
  year         = {2004},
  url          = {https://doi.org/10.1145/1008992.1009004}
}

@article{lv2011lower,
  author       = {Yuanhua Lv and
                  ChengXiang Zhai},
  title        = {Lower-bounding term frequency normalization},
  journal      = {J. Test},
  volume       = {1},
  number       = {2},
  year         = {2011}
}

@misc{froebe2020,
  author       = {Maik Fr{\"{o}}be},
  title        = {Nested {Braces} in {\"{U}}ber-{T}itles},
  year         = {2020}
}

@misc{DBLP:journals/corr/abs-2307-00001,
  editor       = {Ludwig van Beethoven},
  title        = {Encoded {URL}s},
  year         = {2023},
  url          = {https://example.org/a%20b_c}
}
"""


def test_parse_entries() -> None:
    entries = parse_bibtex(BIBTEX)
    assert list(entries) == [
        "fang2004formal",
        "lv2011lower",
        "froebe2020",
        "DBLP:journals/corr/abs-2307-00001",
    ]
    assert entries["fang2004formal"].entry_type == "inproceedings"
    assert entries["fang2004formal"].fields["pages"] == "49–56"
    assert entries["fang2004formal"].bibtex.startswith("@inproceedings{fang2004formal,")
    assert entries["fang2004formal"].bibtex.endswith("}")


def test_authors_and_short_citations() -> None:
    entries = parse_bibtex(BIBTEX)
    assert [author.full_name for author in entries["fang2004formal"].authors] == [
        "Hui Fang",
        "Tao Tao",
        "ChengXiang Zhai",
    ]
    assert entries["fang2004formal"].short_citation == "Fang et al., 2004"
    assert entries["lv2011lower"].short_citation == "Lv and Zhai, 2011"
    assert entries["froebe2020"].short_citation == "Fröbe, 2020"
    # Editors, if there are no authors, and "von" parts belong to the last name.
    editor_entry = entries["DBLP:journals/corr/abs-2307-00001"]
    assert editor_entry.short_citation == "van Beethoven, 2023"


def test_full_citation() -> None:
    entries = parse_bibtex(BIBTEX)
    citation = entries["fang2004formal"].full_citation
    assert citation == (
        "Hui Fang, Tao Tao, and ChengXiang Zhai. "
        '<a href="https://doi.org/10.1145/1008992.1009004">'
        '<span class="title">A formal study of information retrieval heuristics</span>'
        '</a>. In <span class="venue">SIGIR 2004</span>, pages 49–56, 2004.'
    )
    assert (
        '<span class="venue">J. Test</span>, 1 (2), 2011.'
        in entries["lv2011lower"].full_citation
    )
    assert "Nested Braces in Über-Titles" in entries["froebe2020"].full_citation
    # URLs are not LaTeX (e.g., "%" is not a comment).
    url_citation = entries["DBLP:journals/corr/abs-2307-00001"].full_citation
    assert '<a href="https://example.org/a%20b_c">' in url_citation


def test_duplicate_keys() -> None:
    with raises(BibliographyError, match="Duplicate"):
        parse_bibtex(BIBTEX + BIBTEX)


def test_invalid_bibtex() -> None:
    with raises(BibliographyError, match="Invalid"):
        parse_bibtex("@article{broken,\n  title = {Unclosed\n")


def test_process_citations() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    markdown = bibliography.process("See [@fang2004formal, @lv2011lower].")
    assert (
        '<span class="citation">&#91;'
        '<a href="#fang2004formal">Fang et al., 2004</a>; '
        '<a href="#lv2011lower">Lv and Zhai, 2011</a>'
        "&#93;</span>"
    ) in markdown
    assert "## References" in markdown
    assert '<div class="reference" id="fang2004formal">' in markdown
    assert 'id="froebe2020"' not in markdown
    # Sorted by first author.
    assert markdown.index('id="fang2004formal"') < markdown.index('id="lv2011lower"')
    assert '<label for="bibtex-fang2004formal">bib</label>' in markdown
    assert "<code>@inproceedings{fang2004formal," in markdown
    # Raw HTML blocks must not contain blank lines.
    references = markdown[markdown.index("## References") :]
    for block in references.split("\n\n")[1:]:
        assert block.startswith("<div") and block.rstrip().endswith("</div>")


def test_process_citation_separators() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    with_commas = bibliography.process("See [@fang2004formal,@lv2011lower].")
    with_semicolons = bibliography.process("See [@fang2004formal; @lv2011lower].")
    assert with_commas == with_semicolons


def test_process_dblp_keys() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    markdown = bibliography.process("See [@DBLP:journals/corr/abs-2307-00001].")
    assert '<a href="#DBLP:journals/corr/abs-2307-00001">' in markdown
    assert 'id="DBLP:journals/corr/abs-2307-00001"' in markdown


def test_process_without_citations() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    assert bibliography.process("No citations here.") == "No citations here."


def test_process_ignores_code() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    markdown = "Use `[@key]` to cite.\n\n```markdown\n[@unknown]\n```\n"
    assert bibliography.process(markdown) == markdown


def test_process_unknown_key() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    with raises(BibliographyError):
        bibliography.process("See [@unknown].")
