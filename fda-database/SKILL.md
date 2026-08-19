---
name: fda-database
description: Search official FDA/openFDA medication and pill data, including drug labels, NDC product records, recalls/enforcement, adverse-event reports, Drugs@FDA approvals, shortages, and substance identifiers. Use for drug label facts, pill/product identification by NDC or ingredient, warnings, contraindications, recalls, shortages, adverse-event signal checks, and FDA regulatory data. Use entrez-search as a literature fallback, not as the primary source for drug labels.
metadata: {"veles":{"secrets":{"env":["OPENFDA_API_KEY"]}}}
---

# FDA Database

Use official FDA/openFDA data for medication and pill information. Keep this skill focused on regulatory/product facts and safety signals; use `entrez-search` only when literature evidence is needed beyond label/regulatory data.

## Required workflow for medication advice

Before answering patient-facing medication questions:

1. Use `memory_search` for relevant prior conversations, allergies, medication lists, conditions, or user preferences.
2. Read `docs/myhealth` if that path exists in the workspace.
3. Use this skill for FDA label, NDC, recall, shortage, approval, or FAERS signal data.
4. Cross-check important safety claims across at least two appropriate sources when possible, such as label plus recall/shortage data, label plus DailyMed, or FDA label plus `entrez-search` literature.
5. State uncertainty and advise a licensed clinician/pharmacist for dosing changes, interactions, pregnancy/lactation questions, serious symptoms, or urgent safety concerns.

Do not present FAERS/openFDA adverse-event reports as proof that a drug caused a reaction. Treat them as post-market safety signals only.

## Optional API key

Do not require an API key. The script works without one at lower openFDA daily limits.

- Store the optional key in Veles Secrets as `skills.fda-database.env.OPENFDA_API_KEY`.
- The script reads `OPENFDA_API_KEY` first and also accepts `FDA_API_KEY` for compatibility.
- Pass `--api-key` only when the user explicitly provides a key for the run.

## Script workflow

Use `scripts/fda_query.py`:

```bash
python scripts/fda_query.py label --search 'openfda.brand_name:"Advil"' --limit 3
python scripts/fda_query.py ndc --search 'generic_name:"IBUPROFEN"' --limit 5
python scripts/fda_query.py enforcement --search 'product_description:"metformin"' --limit 5
python scripts/fda_query.py event --search 'patient.drug.medicinalproduct:"metformin"' --count patient.reaction.reactionmeddrapt.exact
python scripts/fda_query.py drugshortages --search 'status:"Currently in Shortage"' --limit 10
```

Useful options:

- `endpoint`: one of `label`, `event`, `ndc`, `enforcement`, `drugsfda`, `drugshortages`, `substance`, `device-event`, `device-enforcement`, `food-enforcement`.
- `--search`: openFDA search expression.
- `--count`: aggregation field.
- `--limit`: result count, default `10`.
- `--skip`: pagination offset.
- `--api-key`: optional openFDA key.
- `--fields`: comma-separated fields to print from each result.
- `--raw`: print full JSON.

## Common drug queries

Label by brand or generic:

```bash
python scripts/fda_query.py label --search 'openfda.brand_name:"ELIQUIS"' --fields openfda.brand_name,openfda.generic_name,warnings,boxed_warning,contraindications
```

NDC product lookup:

```bash
python scripts/fda_query.py ndc --search 'product_ndc:"0002-8215"' --raw
```

Recall/enforcement lookup:

```bash
python scripts/fda_query.py enforcement --search 'product_description:"semaglutide"' --fields recall_number,classification,reason_for_recall,status,recall_initiation_date
```

FAERS signal count:

```bash
python scripts/fda_query.py event --search 'patient.drug.medicinalproduct:"warfarin"' --count patient.reaction.reactionmeddrapt.exact
```

Substance lookup:

```bash
python scripts/fda_query.py substance --search 'names.name:"acetaminophen"' --limit 5
```

## Source boundaries

- Prefer FDA label/openFDA label or DailyMed for current prescribing information.
- Prefer NDC records for product/package identity, labeler, route, dosage form, marketing status, and NDCs.
- Prefer enforcement reports for recalls.
- Prefer drug shortages endpoint for current/resolved shortage status.
- Use FAERS adverse events for signal exploration only; do not infer incidence, prevalence, or causality.
- Avoid `drug-labels-search` as a default because it requires a credit-based Valyu API key.
- Do not rely on RxNav for drug-drug interaction checks; its interaction API was discontinued in 2024. RxNorm/RxNav can still be useful later for name/RxCUI normalization.

## References

Read `references/openfda.md` when you need endpoint mapping, query syntax, field examples, FAERS limitations, or responsible-use wording.
