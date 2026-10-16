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
"""


def test_parse_entries() -> None:
    entries = parse_bibtex(BIBTEX)
    assert list(entries) == ["fang2004formal", "lv2011lower", "froebe2020"]
    assert entries["fang2004formal"].entry_type == "inproceedings"
    assert entries["fang2004formal"].fields["pages"] == "49--56"
    assert entries["fang2004formal"].bibtex.startswith("@inproceedings{fang2004formal,")
    assert entries["fang2004formal"].bibtex.endswith("}")


def test_authors_and_short_citations() -> None:
    entries = parse_bibtex(BIBTEX)
    assert entries["fang2004formal"].authors == ["Hui Fang", "Tao Tao", "ChengXiang Zhai"]
    assert entries["fang2004formal"].short_citation == "Fang et al., 2004"
    assert entries["lv2011lower"].short_citation == "Lv and Zhai, 2011"
    assert entries["froebe2020"].short_citation == "Fröbe, 2020"


def test_full_citation() -> None:
    entries = parse_bibtex(BIBTEX)
    citation = entries["fang2004formal"].full_citation
    assert "Hui Fang, Tao Tao, and ChengXiang Zhai." in citation
    assert "**A formal study of information retrieval heuristics.**" in citation
    assert "_SIGIR 2004_" in citation
    assert "49–56" in citation
    assert "1(2)" in entries["lv2011lower"].full_citation
    assert "Nested Braces in Über-Titles" in entries["froebe2020"].full_citation


def test_duplicate_keys() -> None:
    with raises(BibliographyError):
        parse_bibtex(BIBTEX + BIBTEX)


def test_process_citations() -> None:
    bibliography = Bibliography(entries=parse_bibtex(BIBTEX))
    markdown = bibliography.process("See [@fang2004formal; @lv2011lower].")
    assert "([Fang et al., 2004](#fang2004formal); [Lv and Zhai, 2011](#lv2011lower))" in markdown
    assert "## References" in markdown
    assert '<a id="fang2004formal"></a>' in markdown
    assert '<a id="froebe2020"></a>' not in markdown
    # Sorted by first author.
    assert markdown.index('id="fang2004formal"') < markdown.index('id="lv2011lower"')
    assert "```bibtex" in markdown


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


def test_options() -> None:
    bibliography = Bibliography(
        entries=parse_bibtex(BIBTEX), heading="Literature", show_bibtex=False
    )
    markdown = bibliography.process("See [@fang2004formal].")
    assert "## Literature" in markdown
    assert "```bibtex" not in markdown
