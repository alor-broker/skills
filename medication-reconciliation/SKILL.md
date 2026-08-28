---
name: medication-reconciliation
description: "Reconcile medicines, supplements, and allergies, identify discrepancies, and verify local official labeling without prescribing or changing doses. / Сверять лекарства, добавки и аллергии, находить расхождения и проверять местные официальные инструкции без назначения или изменения доз."
---

# Medication Reconciliation

Build a reliable medication list and identify questions that require the prescriber, pharmacist, current label, or regulator. Do not turn an incomplete list into a declaration that a regimen is safe.

## Emergency stop

Possible overdose, severe allergic symptoms, collapse, severe confusion, breathing difficulty, major bleeding, or another acute dangerous reaction takes priority. Tell the user to call the local emergency service or poison service as appropriate; do not continue ordinary reconciliation first.

If a duplicate dose may already have been taken, the next dose is due before the prescriber or pharmacist can be reached, or the amount taken is uncertain, treat this as time-sensitive. Do not choose which product to skip or take. Direct the user promptly to a verified local poison service, urgent medical service, prescriber, or pharmacist. Never invent a poison-service number; if no verified service is available and harm may be serious, use the local emergency service. In Russia, use `112` or `103` for an emergency.

## Collect and verify

For each current, recent, and as-needed item, capture:

- generic and trade name exactly as shown;
- strength, dosage form, route, schedule, and actual use;
- indication, prescriber, start date, recent change, and stop date if relevant;
- prescription medicines, over-the-counter products, vitamins, herbals, supplements, and recreational substances that may matter;
- missed doses, duplicate supplies, access problems, and side effects reported by the user.

Also capture allergies and the actual reaction, age or age range, jurisdiction, pregnancy/breastfeeding status when relevant, kidney or liver disease, relevant conditions, and the source/date of each list. Do not merge similar names or formulations without confirmation.

## Reconcile

1. Compare every source and label discrepancies as omissions, additions, duplicates, dose/form conflicts, timing conflicts, expired orders, or uncertain identity.
2. Ask the user to confirm the list; do not “clean up” a disagreement silently.
3. Check current official labeling and safety communications in the relevant jurisdiction.
4. For the United States, use `fda-database` when available for FDA/openFDA facts. FDA status is not evidence of registration or instructions in another country.
5. For Russia, use the current GRLS record (`https://grls.rosminzdrav.ru/`) and Roszdravnadzor safety information.
6. Use literature evidence only to supplement, not replace, the current official label and clinician judgment.

Review questions such as duplicate therapy, drug-allergy conflict, administration mismatch, high-risk combinations named in authoritative sources, monitoring requirements, organ-function considerations, pregnancy/lactation, and transition-of-care discrepancies. If no validated interaction source is available, say so.

Never say “there are no interactions.” Say “no interaction was found in the sources checked,” name those sources and dates, and state important limitations.

## Boundaries

- Do not tell the user to start, stop, taper, substitute, or change a prescription dose.
- Do not calculate an individualized dose from an incomplete record or a generic table.
- Do not identify an unknown pill by appearance alone.
- Do not infer causality or incidence from spontaneous adverse-event reports such as FAERS.
- Do not treat model memory as a current drug label.
- Direct consequential decisions to the prescriber or pharmacist and provide a concise question for them.

## Output

Return a confirmed/unconfirmed medication table, discrepancies, source-backed safety questions, missing information, urgency, and a short list of questions for the prescriber or pharmacist. Keep facts, user reports, source findings, and inferences visibly separate.

Do not persist the medication list or allergy history without explicit user consent. Encourage removal of names, prescription numbers, barcodes, QR codes, and pharmacy identifiers before external lookup.
