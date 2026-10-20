# ADR-0001: PaySim as the only core source

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

The first complete vertical slice needs one auditable source before adding more datasets or infrastructure. §5.1 designates PaySim (D1), a synthetic mobile-money transaction simulation, as the sole source for ingestion, validation, quality analysis, feature engineering, chronological model evaluation, BI, and API demonstration. Published snapshot claims (about 6,362,620 records, ~0.1291% fraud prevalence) are reference claims, not verified local facts, so Phase 1 must compute exact local counts and prevalence.

**Decision**

- PaySim (D1) is the only mandatory core source for the first vertical slice (§5.1).
- `step` is the primary event-time / split index; it is a synthetic simulation step, not a measured UTC timestamp. Do not fabricate `event_time_utc` by assuming an arbitrary starting date (§5.1).
- Extension datasets (D2-D6) are not required for the core milestone and each requires a separate source audit before use (§5.2).
- Verify license and attribution against the exact downloaded version and record it in the source registry before the data is distributed or republished (§5.1).

**Alternatives considered**

- Multi-source core slice from the start: rejected; violates the small-vertical-slice principle that one source-to-output path must work first (§2 principles).
- Treating published snapshot counts and prevalence as verified facts: rejected; they are reference claims from published descriptions, not facts about the local download (§5.1).

**Consequences and trade-offs**

- Scope is bounded and auditable, but results are specific to synthetic PaySim and must be labeled as synthetic; they do not support production fraud-detection claims (§2 risks).
- Other domains (bank-account fraud, bitcoin graph) are deferred to later phases, delaying those analyses.

**Tests/evidence required**

- Source audit report recording exact local row count, column count, label prevalence, unique time steps, and file hash (§5.1; §14.2 evidence).
- Gate P0 confirms PaySim is the only mandatory source for the first vertical slice (§15 Phase 0).

**Revisit trigger**

Revisit when a second source is required for the core milestone or when a measured requirement justifies the added dataset and infrastructure complexity.

