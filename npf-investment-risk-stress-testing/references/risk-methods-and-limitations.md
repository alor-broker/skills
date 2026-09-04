# Risk methods and limitations

- Volatility summarizes dispersion and is not a loss bound.
- Drawdown depends on the observed path and available history.
- Historical VaR and expected shortfall depend on the sample, horizon, frequency, valuation, and liquidity assumptions; neither captures an omitted regime.
- Parametric VaR is fragile under non-normal tails and unstable correlations.
- Duration and key-rate duration approximate rate sensitivity and must reflect options and curve shape.
- Credit spread, migration, default, and recovery are separate mechanisms.
- Concentration must consider issuer, group, sector, geography, currency, instrument, maturity, collateral, counterparty, and common risk drivers.
- Quoted volume is not executable liquidity. Apply explicit sale horizons, market depth, settlement, and haircut assumptions.
- Correlation is not stable in stress and does not prove causality.

For every metric, record formula, units, horizon, confidence level when applicable, sample, data frequency, missing-data treatment, price source, and limitations. Prefer several complementary measures to one synthetic score.
