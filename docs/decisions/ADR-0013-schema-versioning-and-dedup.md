### ADR-0013: Schema Versioning, Compatibility, and Downstream Deduplication

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

§7.2–§7.4 defines Silver-layer quality actions and source-locator uniqueness, but the original plan did not specify how a canonical contract changes over time, how a downstream reader (Gold, feature pipeline, model training) should react to a schema it does not recognize, or how a business-key duplicate candidate — already flagged, not resolved, at Silver — should be counted once it reaches an aggregated Gold fact table or the ML feature set. Leaving these undefined risks silent reinterpretation of old data under a new contract, or inconsistent duplicate counts across reports.

**Decision**

1. `schema_version` is `MAJOR.MINOR`. A MINOR change is backward-compatible (new optional/nullable field, relaxed constraint) and requires no reprocessing. A MAJOR change is breaking (field removed/renamed/retyped, changed label or identity semantics) and requires reprocessing from Bronze under the new contract; previously committed runs under an earlier MAJOR version remain valid under their own version.
2. Every downstream reader of Silver/Gold output declares the `schema_version` range it accepts and fails closed on a manifest outside that range, per §7.5.
3. A business-key duplicate candidate set, once it reaches Gold or the ML feature pipeline, is resolved per fact table/feature using one explicit, deterministic, documented tie-breaking rule (default: first-by-`source_record_id`), recorded in the metric dictionary (§12.4) alongside any metric it affects, per §7.6. This does not reclassify the candidates at Silver.

**Alternatives considered**

- A schema registry service: rejected at this scale; a declared version range checked at read time is sufficient until evidence shows otherwise (§2.3).
- Silent best-effort field coercion on a schema mismatch: rejected as inconsistent with the fail-closed principle (§3) and the project's semantic-integrity principle (§3).
- Automatic deduplication at Silver (deleting one of two business-key-colliding records): rejected because it would be an unverified judgment about which record is the "true" one; Silver retains both and investigation/aggregation rules live downstream, consistent with the project's non-destructive quarantine philosophy (§7.4).

**Consequences and trade-offs**

Readers must maintain an explicit accepted-version range, adding a small amount of configuration. Gold/ML aggregation rules must be documented per fact table rather than assumed globally, which is more verbose but prevents inconsistent duplicate handling across reports.

**Tests/evidence required**

- A Gold build or feature-pipeline run against a Silver manifest outside its declared `schema_version` range fails closed with a clear error (not a silent partial build).
- A fixture containing a known business-key duplicate candidate set produces the documented tie-break outcome in the relevant fact table, with the excluded-candidate count visible in the data-quality summary.

**Revisit trigger**

Revisit if the number of source datasets or schema revisions grows enough that a declared version range per reader becomes error-prone to maintain by hand, or if a true schema registry provides measured value over the current approach.

