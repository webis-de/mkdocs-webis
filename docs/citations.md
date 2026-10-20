# Citations

<p class="subtitle">Cite references from a BibTeX file by their keys.</p>

With a `bibliography` configured, cite one or more references by their BibTeX keys:

```markdown
Axioms are formal constraints on retrieval models [@fang2004formal].
Some studies use axioms for re-ranking [@hagen2016axiomatic, @bondarenko2022axiomatic].
```

Which renders as:

Axioms are formal constraints on retrieval models [@fang2004formal].
Some studies use axioms for re-ranking [@hagen2016axiomatic, @bondarenko2022axiomatic].

Citations are rendered as gray author–year links in brackets, like on the Webis slides.
Each links to the "References" section at the bottom of the same page, which lists all references cited on that page, sorted by first author.
A journal article looks like this: [@fang2011diagnostic].

## Details

- Separate multiple keys by commas (semicolons work, too).
- Citations inside inline code or code blocks are not replaced, as in the example above.
- Citations in content that other plugins insert while rendering a page (e.g., API docstrings from [mkdocstrings](https://mkdocstrings.github.io/)) are replaced, too, and their references are added to the "References" section.
- Unknown keys and invalid BibTeX files fail the build.
- LaTeX markup in the BibTeX fields (e.g., `{\"{o}}` for "ö") is converted to plain text.

We recommend copying BibTeX entries from [DBLP](https://dblp.org/).
