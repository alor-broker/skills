# Model validation checklist

- Purpose and failure condition are explicit.
- Inputs have identified sources, dates, access classifications, units, and definitions.
- Formula, implementation, and transformations can be reproduced.
- Missing and stale data treatment is visible.
- Price, liquidity, default, recovery, dependency, and optionality assumptions are explicit.
- Results reconcile to simple benchmarks or independent calculations where possible.
- Sensitivities show which assumptions drive the answer.
- Backtesting is used only when the metric and data permit it.
- The model has plausible boundary, sign, and extreme-shock behavior.
- Limitations and out-of-scope exposures accompany the result.
- The strongest independent objection is recorded and answered or left as a decisive caveat.

Passing these checks supports reproducibility but does not by itself provide model approval, regulatory validation, or authority to act. Failure of a material check makes the result exploratory and must be visible in the decision record.
