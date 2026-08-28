---
name: fda-database
description: "Search official United States FDA/openFDA drug labels, products, recalls, reports, approvals, and shortages; use the local regulator elsewhere. / Искать официальные сведения FDA/openFDA США об инструкциях, препаратах, отзывах, сообщениях, одобрениях и дефиците; для других стран использовать местный регулятор."
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
- The script reads only the injected `OPENFDA_API_KEY` environment value. Never put the key in command arguments or output.

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

- FDA/openFDA is specific to the United States. Ask for jurisdiction before applying regulatory information. For Russia, verify the current GRLS record and Roszdravnadzor safety material; do not present FDA status as Russian registration or instructions.
- Prefer FDA label/openFDA label or DailyMed for current prescribing information.
- Prefer NDC records for product/package identity, labeler, route, dosage form, marketing status, and NDCs.
- Prefer enforcement reports for recalls.
- Prefer drug shortages endpoint for current/resolved shortage status.
- Use FAERS adverse events for signal exploration only; do not infer incidence, prevalence, or causality.
- Avoid `drug-labels-search` as a default because it requires a credit-based Valyu API key.
- Do not rely on RxNav for drug-drug interaction checks; its interaction API was discontinued in 2024. RxNorm/RxNav can still be useful later for name/RxCUI normalization.

## References

Read `references/openfda.md` when you need endpoint mapping, query syntax, field examples, FAERS limitations, or responsible-use wording.
