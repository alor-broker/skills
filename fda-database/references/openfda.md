# openFDA Reference

Use this reference for FDA/openFDA medication, product, and safety-signal lookups.

## Official API facts

- Base URL: `https://api.fda.gov`
- Optional key parameter: `api_key`
- No-key standard limits: 240 requests/minute per IP and 1,000 requests/day per IP.
- Free key standard limits: 240 requests/minute per key and 120,000 requests/day per key.
- Use HTTPS for all queries.

## Endpoint map

| Skill endpoint | openFDA path | Best for |
| --- | --- | --- |
| `label` | `/drug/label.json` | Structured product labeling: warnings, indications, contraindications, dosage, adverse reactions |
| `event` | `/drug/event.json` | FAERS adverse-event and medication-error reports |
| `ndc` | `/drug/ndc.json` | NDC product and package records |
| `enforcement` | `/drug/enforcement.json` | Drug recalls and enforcement actions |
| `drugsfda` | `/drug/drugsfda.json` | Drugs@FDA approvals and submissions |
| `drugshortages` | `/drug/shortages.json` | Current and resolved shortages |
| `substance` | `/other/substance.json` | UNII/substance identifiers and names |
| `device-event` | `/device/event.json` | Device adverse-event reports |
| `device-enforcement` | `/device/enforcement.json` | Device enforcement reports |
| `food-enforcement` | `/food/enforcement.json` | Food recall/enforcement reports |

## Query syntax

Common URL parameters:

- `search`: query expression, such as `openfda.brand_name:"ELIQUIS"`.
- `limit`: number of results to return.
- `skip`: offset for pagination.
- `count`: aggregate counts by a field, often with `.exact`.

Useful patterns:

```text
openfda.brand_name:"ADDERALL"
openfda.generic_name:"METFORMIN"
openfda.substance_name:"IBUPROFEN"
product_ndc:"0002-8215"
product_description:"metformin"
patient.drug.medicinalproduct:"warfarin"
receivedate:[20250101+TO+20260524]
```

Use exact fields for aggregations:

```text
patient.reaction.reactionmeddrapt.exact
openfda.brand_name.exact
classification.exact
status.exact
```

## Medication workflows

Label and warnings:

1. Search `label` by `openfda.brand_name`, `openfda.generic_name`, `openfda.substance_name`, NDC, or application number.
2. Extract label sections such as `boxed_warning`, `warnings`, `warnings_and_cautions`, `contraindications`, `indications_and_usage`, `dosage_and_administration`, `drug_interactions`, `pregnancy`, `adverse_reactions`, and `medication_guide`.
3. If the answer is patient-facing, confirm current label context with DailyMed or another official label source when practical.

Pill/product identity:

1. Search `ndc` by NDC, brand, generic, labeler, route, dosage form, or active ingredient.
2. Report product name, generic name, active ingredients, dosage form, route, marketing status, labeler, package NDCs, and effective dates if present.
3. Do not identify a pill from appearance alone unless an official imprint/image source is available.

Recalls and shortages:

1. Search `enforcement` for product descriptions, recall numbers, classification, or status.
2. Search `drugshortages` for current and resolved shortages.
3. Include dates and status because recall/shortage data is time-sensitive.

FAERS/adverse-event signals:

1. Search `event` by medicinal product, active substance, reaction term, date range, age, sex, or seriousness.
2. Use `count` to summarize reaction terms or report dates.
3. State that FAERS reports are voluntarily reported, incomplete, not extensively validated, and cannot prove causation or incidence.
4. Do not use FAERS alone for clinical decisions.

## Medical-answer guardrails

- Search memory first for patient-specific context.
- Read `docs/myhealth` if it exists before answering patient-specific medication questions.
- Ask for missing essentials when needed: exact drug name, dose, route, age, pregnancy/lactation status, allergies, conditions, other meds, and country.
- Warn users to seek urgent care for severe allergic reaction, chest pain, breathing trouble, overdose, suicidal ideation, severe bleeding, or other emergency symptoms.
- Do not instruct users to start, stop, or change medication doses without clinician guidance.
- Use `entrez-search` for literature evidence and guideline-level context; use this skill for FDA product/regulatory facts.

## Related official sources

- openFDA authentication and rate limits: `https://open.fda.gov/apis/authentication/`
- openFDA drug endpoints: `https://open.fda.gov/apis/drug/`
- openFDA drug adverse event limitations: `https://open.fda.gov/apis/drug/event/`
- DailyMed REST API for current SPL labels: `https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm`
- RxNav/RxNorm APIs for drug-name/RxCUI normalization: `https://lhncbc.nlm.nih.gov/RxNav/`
