---
name: npf-investment-risk-stress-testing
description: "Analyze market, credit, concentration, liquidity, counterparty, and model risk and construct stress scenarios for NPF investment decisions. / Анализировать рыночный, кредитный, концентрационный, ликвидный, контрагентский и модельный риск и строить стресс-сценарии для решений НПФ."
---

# NPF Investment Risk and Stress Testing

Analyze market, interest-rate, credit, concentration, currency, liquidity, counterparty, and model risk for Russian pension assets. Use historical, hypothetical, reverse, or organization-specific scenarios as supported by the available evidence.

## Work with the available context

Use portfolio data, risk parameters, sources, and assumptions already supplied or obtained through authorized systems. Do not prompt for holdings, weights, transactions, counterparties, limits, risk appetite, liabilities, internal models, reports, regulatory files, or account data. When a decisive exposure is absent, identify the blind spot and continue with conditional conclusions or sensitivity ranges.

Preserve source lineage and confidentiality classification. Keep internal portfolio facts separate from public market evidence. External data retrieval should not include organization-specific details unless the user has explicitly authorized the destination and purpose.

## Build a defensible risk analysis

Read [references/risk-methods-and-limitations.md](references/risk-methods-and-limitations.md) to select metrics, [references/russian-stress-scenario-design.md](references/russian-stress-scenario-design.md) for Russian-market scenarios, and [references/model-validation-checklist.md](references/model-validation-checklist.md) before relying on model output.

Identify the portfolio or analytical scope, pension regime, valuation date, horizon, data frequency, price convention, currency, coverage, and omitted risk factors. Verify dates and detect stale or frozen prices, truncated histories, corporate actions, survivorship bias, illiquid observations, changing market regimes, and non-tradable periods.

Use historical episodes as mechanisms rather than mechanical templates. State each shock, transmission channel, dependency assumption, liquidity haircut, recovery assumption, and valuation rule. Add reverse stress testing when the failure condition is more informative than an arbitrary shock. Do not attach probabilities without a validated basis.

Separate model output from judgment. Show formulas, inputs, transformations, and sensitivities. Construct the strongest objection a risk officer or model validator would make and make unresolved weaknesses visible in the conclusion.

## Output

Return the risk question, scope, data cutoff, methods, assumptions, scenario table, sensitivity, coverage gaps, model limitations, strongest objection, decision implications, and owners of further review. Distinguish financial stress analysis from the current mandatory Bank of Russia methodology, a formal regulatory result, and internal limit approval; use `npf-asset-management-legal-review` for legal applicability. Respond in the user's language with equivalent safeguards.
