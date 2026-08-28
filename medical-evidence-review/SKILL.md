---
name: medical-evidence-review
description: "Find and synthesize current guidelines, regulator information, and appropriate research for a focused medical question. / Искать и сопоставлять действующие рекомендации, сведения регуляторов и подходящие исследования для конкретного медицинского вопроса."
---

# Medical Evidence Review

Answer focused medical questions from current, applicable evidence rather than model memory or search snippets.

## Frame the question

Clarify the population, condition or exposure, intervention or index test, comparator, outcome, care setting, jurisdiction, and time horizon as applicable. For patient-specific questions, separate supplied facts from assumptions and do not silently fill missing criteria.

If the request describes a possible emergency, stop the review flow and give the local emergency action first.

## Match evidence to the question

There is no single hierarchy that fits every medical question.

- Treatment and prevention: current applicable guidelines, systematic reviews, and randomized trials.
- Diagnosis: current diagnostic guidance and diagnostic-accuracy studies in the intended population and setting.
- Prognosis or risk: externally validated cohorts or models with calibration and applicability information.
- Medication use: the current local regulator-approved label and safety communications, then supporting studies.
- Harms: regulator warnings, trials, observational evidence, and pharmacovigilance signals with their distinct limitations.
- Rare conditions: authoritative disease resources, case series, and primary studies, with the evidence scarcity made explicit.

Start with the user’s jurisdiction. For Russia, check the Ministry of Health clinical-recommendation rubricator (`https://cr.minzdrav.gov.ru/`), the state medicines register (`https://grls.rosminzdrav.ru/`), and current Roszdravnadzor safety material. For other jurisdictions, use the corresponding regulator and recognized guideline body. Compare WHO or another relevant international source when local and international recommendations materially differ.

For an explicit cross-jurisdiction comparison, keep separate sections for each jurisdiction’s registration status, regulator-approved labeling, and clinical recommendations, followed by a third section for shared international or scientific evidence. Absence of a located current document is “not found after the stated search,” not evidence of non-registration, prohibition, or a negative recommendation.

When `entrez-search` is available, use it for PubMed, PMC, ClinVar, and related NCBI retrieval. Search by concepts and controlled vocabulary, not only a natural-language sentence. Derive date limits from the current date and the clinical question; do not reuse a stale fixed year range.

## Source integrity

- Open and read the source; a search snippet is not evidence.
- Record title, issuing organization or journal, jurisdiction/population, publication or update date, access date, and stable identifier or URL.
- Verify that the recommendation applies to the patient group, setting, intervention, formulation, and outcome under discussion.
- Preserve the source’s strength or certainty rating when available; do not invent one.
- Identify retractions, major corrections, superseded guidelines, and conflicts of interest when material.
- Show meaningful conflicts between sources instead of silently choosing one.
- Treat preprints, news, commercial summaries, pharmacovigilance reports, and computational predictions according to their limitations.
- Verify citations and identifiers before presenting them. Never generate a plausible-looking reference from memory.

If a current authoritative source cannot be verified, abstain from action-level advice and say what could not be established.

## Synthesis

Return:

1. the focused question and scope;
2. bottom line with calibrated uncertainty;
3. evidence by source type and applicability;
4. agreements and conflicts;
5. limitations and missing patient information;
6. what the evidence supports, does not support, and leaves uncertain;
7. exact sources with dates and links.

For patient-facing answers, translate technical conclusions into plain language without turning population evidence into a personal diagnosis or prescription. For clinicians, preserve effect estimates, confidence intervals, absolute risks, and evidence certainty when the source supplies them.

Do not send identifiable health information to external searches. De-identify the query and keep the mapping local.
