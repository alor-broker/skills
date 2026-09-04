---
name: npf-reporting-quality-review
description: "Review definitions, lineage, consistency, and reproducibility of NPF, asset-manager, market, issuer, or management reporting. / Проверять определения, происхождение, согласованность и воспроизводимость отчётности НПФ, УК, рынка, эмитента или управленческих материалов."
---

# NPF Reporting Quality Review

Review whether financial, performance, market, regulatory, or management evidence is reliable enough for the intended analytical use. Check data lineage, metric definitions, periods, units, formulas, revisions, and consistency. This is an analytical quality review, not an audit opinion or regulatory attestation.

## Work with the available context

Use reports, extracts, tables, and source links already supplied or obtained through authorized systems. Do not prompt for internal reports, accounting extracts, regulatory working files, special-depositary files, portfolios, limits, agreements, committee papers, reconciliations, account data, or credentials. When a source needed for reconciliation is absent, state the limitation and the control owner instead of requesting disclosure.

Classify every source as public, internal, third-party, calculated, or assumed. Preserve access classification and keep non-public material out of external search queries and third-party tools unless the user explicitly authorizes the destination and purpose.

## Inspect the evidence

Read [references/report-quality-checklist.md](references/report-quality-checklist.md) for the review. Use [references/metric-definitions.md](references/metric-definitions.md) when a metric can be defined more than one way and [references/source-lineage.md](references/source-lineage.md) to record transformations.

Confirm source owner, document identity, publication or preparation date, observation period, regime, entity and consolidation perimeter, reporting basis, review status, units, currency, scale, sign convention, gross or net basis, valuation convention, and revision history.

Recalculate material totals, ratios, growth, returns, and comparisons from the available inputs. Preserve formulas and rounding. Distinguish missing, not provided, not applicable, zero, and suppressed. Compare tables only after reconciling period, perimeter, units, denominators, and definitions.

Treat footnotes, methodology, control status, restatements, and errata as part of the data. Keep regulator aggregates, issuer reports, internal management views, rating opinions, broker estimates, and news in their proper evidentiary roles.

Construct the strongest objection an auditor, controller, data-quality lead, or skeptical investment-committee member would make. If the evidence cannot answer it, mark the figure unsuitable for the proposed use.

## Output a quality decision

Return the intended use, evidence inventory, definition and lineage table, recalculations, inconsistencies, revisions, unresolved objections, and one of:

- **usable for the stated purpose**;
- **usable only with stated qualifications**;
- **not reproducible from the available evidence**;
- **not comparable**.

Do not describe the result as an audit opinion, formal reconciliation, or confirmation of regulatory compliance. Respond in the user's language with equivalent safeguards.
