# ADR-0004: Default exclusion of `isFlaggedFraud` and the four balance fields

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

PaySim includes fields that require special treatment before modeling. §5.1 flags `isFlaggedFraud` as a source-provided rule needing special treatment, and excludes balance fields `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, and `newbalanceDest` from the default predictive feature set because the simulation's fraud/cancellation behavior makes them problematic predictors. §21 lists leakage/simulator artifacts in balance and flag fields as a risk that can artificially inflate metrics.

**Decision**

- Exclude `isFlaggedFraud` and the four balance fields (`oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`) from the default predictive feature set (§5.1).
- `isFlaggedFraud` may be used only as a source-provided diagnostic / reference rule, not as a predictor or a substitute for chronological out-of-time evaluation (§11.1).
- Keep any diagnostic-only PaySim balance-artifact analysis separate from the approved model feature set (§15 Phase 1).

**Alternatives considered**

- Include balance fields as predictors: rejected; the dataset documentation warns they are unsuitable due to fraud/cancellation behavior, and §21 treats simulator-artifact leakage as a metric-inflation risk (§5.1, §21).
- Treat `isFlaggedFraud` as the model target: rejected; the label is `isFraud`, while `isFlaggedFraud` is a separate source-provided rule (§5.1).

**Consequences and trade-offs**

- Prevents leakage and simulator-artifact inflation; keeps the approved serving feature set small, explicit, and auditable.
- Balance-field insights are deferred to labeled diagnostic experiments and are not available for serving.

**Tests/evidence required**

- Temporal / leakage tests assert that target and forbidden columns (including excluded balance fields and `isFlaggedFraud`) never enter the feature matrix (§14.1).
- Run the diagnostic-only balance-artifact analysis and keep its rule and result separate from the approved model feature set (§15 Phase 1).

**Revisit trigger**

Revisit if the Phase 4 diagnostic analysis produces evidence that a balance field is legitimately predictive and a written rationale is approved.

