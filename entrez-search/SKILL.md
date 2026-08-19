---
name: entrez-search
description: Search and retrieve biomedical/scientific records through NCBI Entrez E-utilities, including PubMed, PMC, Gene, Protein, Nuccore, ClinVar, PubChem, MeSH, and SNP. Use for literature search, abstracts, PMIDs, gene/protein lookup, ClinVar records, and NCBI cross-database retrieval. For drug labels use fda-database, not Entrez.
metadata: {"veles":{"secrets":{"env":["NCBI_API_KEY"]}}}
---

# Entrez Search

Use NCBI Entrez E-utilities for biomedical literature and NCBI database retrieval. Keep this as the single active PubMed/Entrez skill; do not install overlapping PubMed-only skills unless the user explicitly wants a separate skill.

## Dependencies

The bundled script only needs `requests`:

```bash
pip install requests
```

## Optional NCBI identity

Do not require `email` or `api_key` for normal use.

- Use `--email` or `NCBI_EMAIL` when the user provides an email or the query is large.
- Use `--api-key` or the injected `NCBI_API_KEY` secret when configured. Veles exposes this optional target as `skills.entrez-search.env.NCBI_API_KEY`.
- Use `--tool` to identify the client; the script defaults to `veles-entrez-search`.

## Databases

| База | Описание | db |
|------|----------|----|
| pubmed | Медицинская литература | pubmed |
| pmc | Полные тексты / PubMed Central | pmc |
| gene | Гены | gene |
| protein | Белковые последовательности | protein |
| nucleotide | Нуклеотидные записи | nuccore |
| clinvar | Клинические варианты | clinvar |
| pubchem_compound | Химические соединения PubChem | pccompound |
| pubchem_substance | Вещества PubChem | pcsubstance |
| pubchem_assay | BioAssay PubChem | pcassay |
| mesh | MeSH vocabulary | mesh |
| snp | dbSNP variants | snp |

## Script workflow

Use the bundled script for reliable ESearch, ESummary, and PubMed abstract retrieval:

```bash
python scripts/entrez_search.py --db pubmed --term "cancer treatment" --retmax 5
```

Common options:

- `--db`: E-utilities database name, for example `pubmed`, `pmc`, `gene`, `protein`, `nuccore`, `clinvar`, `pccompound`, `pcsubstance`, `pcassay`, `mesh`, `snp`.
- `--term`: Entrez query.
- `--retmax`: maximum results, default `10`.
- `--retstart`: result offset for paging.
- `--sort`: sort order, for example `relevance` or `date`.
- `--summary`: run ESummary for returned IDs.
- `--abstracts`: run PubMed EFetch for abstracts.
- `--rettype`: EFetch `rettype` for `--abstracts`, default `abstract`.
- `--email`, `--api-key`, `--tool`: optional NCBI identity parameters.

For latest/recent medical evidence in PubMed, prefer `--sort date` and include a date filter:

```bash
python scripts/entrez_search.py --db pubmed --sort date --retmax 10 --summary \
  --term "(asthma[mh] OR asthma[tiab]) AND (systematic review[pt] OR meta-analysis[pt]) AND 2020:2026[dp] AND hasabstract[text]"
```

## Medical search strategy

For medical questions, prefer high-quality evidence first:

1. Guidelines
2. Systematic reviews / meta-analyses
3. Randomized controlled trials
4. Large observational studies
5. Case reports only when evidence is sparse

Useful PubMed filters:

- `systematic review[pt]`
- `meta-analysis[pt]`
- `randomized controlled trial[pt]`
- `clinical trial[pt]`
- `guideline[pt]`
- `practice guideline[pt]`
- `2020:2026[dp]`
- `english[la]`
- `hasabstract[text]`
- `free full text[sb]`

Use MeSH when possible:

- `diabetes mellitus, type 2[mh]`
- `hypertension[mh]`
- `asthma[mh]`
- `myocardial infarction[mh]`

Example evidence-first query:

```text
(asthma[mh] OR asthma[tiab])
AND (treatment[tiab] OR therapy[tiab])
AND (systematic review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt])
AND 2020:2026[dp]
AND hasabstract[text]
```

For patient-facing medical answers, do not cite a single low-quality paper as if it proves clinical guidance.

## Advanced retrieval

Read `references/api_reference.md` when you need ELink related-article discovery, EPost/history-server batch workflows, citation matching, or a broader query-syntax refresher.

## Limits

- NCBI recommends no more than 3 requests/second without an API key.
- An API key raises the default limit to 10 requests/second.
- Use `tool` and `email` values for large or repeated workflows.
- Use EPost/history server for large result sets instead of paging thousands of IDs by hand.
