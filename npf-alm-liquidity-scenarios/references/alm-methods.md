# ALM methods

## Method selection

- Cash-flow matching compares dated asset cash flows with dated liabilities or illustrative liability assumptions. It is sensitive to defaults, calls, prepayments, taxes, and reinvestment.
- Duration matching requires both the present-value gap and monetary rate sensitivity to be controlled. Compare `present value × modified duration` or PVBP for assets and liabilities; equal percentage durations alone do not immunize unequal present values. It does not match cash flows and can fail under non-parallel curve moves or changing options.
- Convexity adds second-order sensitivity but does not repair poor cash-flow or liquidity assumptions.
- Key-rate duration exposes curve-shape risk by maturity bucket.
- Liquidity ladders compare cash needs with cash and assets under explicit sale horizons and haircuts.
- Stochastic ALM requires justified distributions, dependencies, behavior assumptions, and validation. It is not warranted merely because a simulation tool is available.

## Minimum calculation record

Record valuation date, currency, cash flows, discount curve and date, compounding convention, day count, price basis, optionality, default and recovery assumptions, liquidity haircuts, reinvestment rule, and rounding.

State the coverage limit of the input data. Sector aggregates can inform benchmarks and scenarios but do not replace organization-specific cash flows.
