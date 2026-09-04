---
name: npf-pension-asset-strategy
description: "Analyze Russian NPF pension-asset strategy and synthesize market, issuer, risk, ALM, and performance evidence for executive decisions. / Анализировать стратегию пенсионных активов НПФ и объединять рыночные, эмитентские, риск-, ALM- и результативные данные для решений руководства."
---

# NPF Pension-Asset Strategy

Prepare a decision-useful second opinion about Russian pension-asset strategy. Use this skill for cross-cutting questions that combine market conditions, asset-class roles, issuer evidence, risk, asset-liability considerations, performance, and implementation constraints.

## Work with the available context

Use the question, cited sources, and materials already supplied. Do not prompt the user to upload or disclose organization-specific portfolios, liabilities, limits, agreements, committee materials, account records, or planned transactions. When a decisive input is absent, record it as a decision dependency and continue with the strongest supportable general or conditional analysis.

Classify evidence as public, user-supplied, calculated, assumed, or unknown. Keep organization-specific material separate from externally verified facts. External searches and third-party tools should use public information unless the user has explicitly authorized a suitable destination for the specific material.

## Frame the decision

Identify the acting entity, objective, decision date, horizon, and whether the discussion concerns pension savings or pension reserves. Within pension reserves, distinguish non-state pension provision from the long-term savings program, apply their shared reserve framework first, and then identify program-specific rules or metrics.

Define every material metric, including period, currency, valuation basis, benchmark, inflation measure, and gross or net fee treatment. Read [references/performance-methods.md](references/performance-methods.md) when comparing returns or benchmarks. Read [references/strategy-framework.md](references/strategy-framework.md) for a cross-cutting review and [references/conflict-review.md](references/conflict-review.md) when relationships or incentives could distort the conclusion.

## Build the analysis

1. State the decision question, available evidence, missing dependencies, and who owns the final decision.
2. Set a source cutoff date. Prefer the Bank of Russia, official legal publication, Moscow Exchange, Rosstat, Ministry of Finance, original issuer disclosures, and identified internal sources already supplied.
3. Separate facts, source claims, estimates, assumptions, calculations, and judgment.
4. Compare plausible strategic options by objective, horizon, expected return mechanism, liquidity role, inflation sensitivity, risk, implementation cost, reversibility, and operational dependency.
5. Use the narrower issuer, market, risk, ALM, or reporting-quality skill when it materially improves the answer. Apply `npf-reporting-quality-review` to material numerical conclusions.
6. Construct the strongest objection an experienced pension CIO, risk officer, actuary, auditor, or investment-committee member would make. If it remains unresolved, carry it into the recommendation instead of hiding it.
7. Route legal applicability, asset eligibility, mandatory limits, licence questions, and regulatory compliance to `npf-asset-management-legal-review` and authorized staff. Financial analysis may explain the economic mechanism but must distinguish that from a legal or compliance conclusion.

## Return a decision record

Lead with the conclusion, confidence, and decision status. Then state the regime, date, scope, evidence table, metric definitions, calculations, scenarios, strongest objection, material trade-offs, missing dependencies, recommended option, conditions that would change it, and the responsible internal reviewer or approver.

Distinguish analytical recommendations from portfolio authorization, order placement, formal valuation approval, regulatory reporting, and compliance attestation. Respond in the user's language; Russian and English answers must preserve the same scope, definitions, safeguards, and certainty.
