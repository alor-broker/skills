# Entrez API Reference

Use this reference when the basic `scripts/entrez_search.py` workflow is not enough.

## Core endpoints

Base URL:

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

| Endpoint | Use |
| --- | --- |
| `esearch.fcgi` | Search a database and return IDs |
| `esummary.fcgi` | Return document summaries for IDs |
| `efetch.fcgi` | Retrieve full records, abstracts, XML, FASTA, or database-specific payloads |
| `elink.fcgi` | Find related records across NCBI databases |
| `epost.fcgi` | Upload ID lists for batch/history-server workflows |
| `einfo.fcgi` | Inspect database fields, links, and metadata |

## Common parameters

- `db`: E-utilities database name.
- `term`: query string for `esearch`.
- `id`: comma-separated IDs for `esummary`, `efetch`, or `elink`.
- `retmax`: maximum returned IDs.
- `retstart`: offset for paging.
- `sort`: database-specific sort, for PubMed often `relevance` or `date`.
- `rettype`: return type for `efetch`, for example `abstract`, `medline`, `xml`, `fasta`, or ClinVar-specific `vcv`.
- `retmode`: output mode, commonly `json`, `xml`, or `text`.
- `tool`: client identifier.
- `email`: maintainer contact, optional but recommended for repeated workflows.
- `api_key`: optional NCBI API key. Prefer the Veles secret target `skills.entrez-search.env.NCBI_API_KEY`.
- `usehistory=y`: store results on the NCBI history server for large workflows.
- `WebEnv` and `query_key`: history-server values returned by `esearch`/`epost`.

## Database names

| Domain | db |
| --- | --- |
| PubMed literature | `pubmed` |
| PubMed Central full text | `pmc` |
| Gene | `gene` |
| Protein | `protein` |
| Nucleotide | `nuccore` |
| ClinVar | `clinvar` |
| PubChem Compound | `pccompound` |
| PubChem Substance | `pcsubstance` |
| PubChem BioAssay | `pcassay` |
| MeSH | `mesh` |
| SNP | `snp` |

## Query syntax reminders

- Combine concepts with `AND`, `OR`, and `NOT`.
- Use field tags: `[ti]`, `[tiab]`, `[au]`, `[1au]`, `[ta]`, `[dp]`, `[pt]`, `[mh]`, `[majr]`, `[pmid]`, `[doi]`, `[pmc]`.
- Use MeSH for controlled vocabulary: `diabetes mellitus, type 2[mh]`.
- Use publication types for evidence filters: `systematic review[pt]`, `meta-analysis[pt]`, `randomized controlled trial[pt]`, `guideline[pt]`.
- Use date ranges: `2020:2026[dp]`.
- Add `hasabstract[text]`, `english[la]`, or `free full text[sb]` only when those filters match the user's goal.

## Medical workflows

Basic literature search:

1. Identify the main concepts and synonyms.
2. Combine MeSH terms with title/abstract terms.
3. Start broad, review results, then add publication type, date, language, or abstract filters.
4. Use `--sort date` when the user asks for latest or recent evidence.

Systematic-review style search:

1. Define the PICO question.
2. Include synonyms and MeSH terms for each concept.
3. Prefer high-quality filters first: guidelines, systematic reviews, meta-analyses, RCTs.
4. Document the exact query and search date.
5. Use `usehistory=y` or EPost when the result set is large.

Citation discovery:

1. Search by known PMID, DOI, author, journal, volume, page, or year.
2. Use `elink.fcgi?dbfrom=pubmed&db=pubmed&id=<PMID>&cmd=neighbor` for related PubMed articles.
3. Explore MeSH terms on relevant articles and build refined searches from them.

ClinVar:

- Use `db=clinvar`.
- Use `esearch` for identifiers, `esummary` for overviews, `elink` for related PubMed/MedGen records, and `efetch` for XML.
- Common `efetch` return types include `vcv` for variant records and `clinvarset` for RCV accessions.

## Large and batch queries

- Use `retstart` for simple paging over small result sets.
- Use `usehistory=y` when the result set is large or multiple downstream fetches are needed.
- Use `epost.fcgi` to upload known IDs and then fetch batches with `WebEnv` and `query_key`.
- Cache repeated results locally when building monitoring or extraction workflows.
- Add exponential backoff around rate-limit or transient HTTP failures for production scripts.

## Rate and safety notes

- Without an API key, stay at or below 3 requests/second.
- With an API key, the default limit is 10 requests/second.
- Always include `tool`; include `email` when the user provided one or the job is repeated/large.
- Use `timeout`, `raise_for_status()`, and clear error handling in custom scripts.
- Do not store API keys directly in `SKILL.md`, command examples, or docs.
