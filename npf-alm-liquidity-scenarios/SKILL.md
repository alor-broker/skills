---
name: npf-alm-liquidity-scenarios
description: "Analyze NPF asset-liability alignment, duration, cash-flow matching, and liquidity scenarios from supplied or sourced data. / Анализировать согласование активов и обязательств НПФ, дюрацию, денежные потоки и сценарии ликвидности по имеющимся данным."
---

# NPF ALM and Liquidity Scenarios

Analyze asset-liability alignment, duration, convexity, cash-flow matching, reinvestment risk, and liquidity ladders for Russian pension contexts. Use the detail supported by the available data and state when the result is methodological, conditional, or organization-specific.

## Work with the available context

Use materials and figures already supplied or obtained from authorized sources. Do not prompt for liability schedules, actuarial assumptions, holdings, limits, mandates, agreements, internal models, reports, or account data. If a decisive input is absent, describe the resulting limitation and provide a conditional or illustrative analysis without turning the gap into a disclosure request.

Preserve the source, date, unit, confidentiality classification, and calculation lineage of each material input. Keep internal assumptions separate from public market data, and do not send organization-specific inputs to external tools without explicit authorization for that destination and purpose.

## Select the appropriate depth

- **Method explanation:** explain a concept without organization-specific calculation.
- **Illustrative scenario:** use transparent assumptions to demonstrate mechanics.
- **Portfolio analysis:** use supplied data, identify coverage and data-quality limits, and avoid filling gaps silently.

Read [references/alm-methods.md](references/alm-methods.md) for method selection and [references/liquidity-scenarios.md](references/liquidity-scenarios.md) for scenario design.

## Analyze carefully

Identify whether the analysis concerns pension savings or pension reserves. Within pension reserves, distinguish non-state pension provision from the long-term savings program. Define horizon, currency, inflation basis, discount curve, valuation date, cash-flow timing, optionality, and reinvestment assumptions.

Separate cash-flow matching, present-value matching, duration or PVBP matching, and stochastic analysis. Show formulas and input lineage. Test sensitivity to rates, inflation, credit events, payment timing, participant behavior, market liquidity, and forced-sale discounts without assigning unsupported probabilities.

Construct the strongest objection an actuary, ALM specialist, treasurer, or risk officer would make. Typical objections include omitted options, unstable behavior assumptions, an inconsistent discount curve, stale valuations, and treating quoted assets as immediately liquid.

## Output

State the scope, data coverage, formulas, results, sensitivities, strongest objection, model limitations, and decision dependencies. Distinguish the analytical result from actuarial sign-off, formal funding assessment, internal limit control, and regulatory compliance. Respond in the user's language with equivalent Russian and English safeguards.
