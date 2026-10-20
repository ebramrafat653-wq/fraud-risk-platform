# ADR-0010: Default PaySim balance-field exclusion is a baseline safeguard; simulator-artifact diagnostics are separate experiments

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

§5.1 excludes balance fields `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, and `newbalanceDest` from the default predictive feature set because PaySim's simulated fraud/cancellation behavior makes them problematic predictors. §9.1 clarifies this exclusion is **not** a missing baseline safeguard and does not block Phase 0; the exact balance/label relationship must be measured on the selected source snapshot rather than described as deterministic. `isFlaggedFraud` is excluded from predictors by default and may be reported separately as a source-provided flag/rule benchmark (§9.1).

**Decision**

1. Exclude `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, and `newbalanceDest` from the default predictive feature set (§5.1, §9.1).
2. Balance-field exclusion is a baseline safeguard, not a missing piece blocking Phase 0 (§9.1).
3. Simulator-artifact diagnostics (e.g., whether balance columns are unusually predictive of the synthetic label) are Phase 4 diagnostic-only and kept separate from the approved serving model (§9.1).
4. `isFlaggedFraud` is excluded from predictors by default; it may be reported separately as a source-provided flag/rule benchmark (§9.1).

**Alternatives considered**

- Include balance fields as predictors by default: rejected; simulator behavior may encode rules or artifacts that do not generalize to live payment systems (§5.1, §9.1).
- Treat balance-field diagnostic analysis as part of the approved baseline: rejected; diagnostics are separate experiments and do not authorize excluded columns for use (§9.1).

**Consequences and trade-offs**

- Prevents leakage and simulator-artifact inflation in the baseline serving feature set; keeps it small, explicit, and auditable.
- Balance-field insights are deferred to labeled Phase 4 diagnostics and are unavailable for serving.

**Tests/evidence required**

- Temporal/leakage tests assert target and forbidden columns (including the four balance fields and `isFlaggedFraud`) never enter the feature matrix (§14.1).
- Phase 4 diagnostic reports, if run, are labelled, compared with the approved baseline, and kept separate from the serving model (§9.1).

**Revisit trigger**

Revisit if Phase 4 diagnostic analysis produces evidence that a balance field is legitimately predictive and a written rationale is approved.

