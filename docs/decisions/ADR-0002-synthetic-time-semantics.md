# ADR-0002: Synthetic time semantics; no fabricated source-observed UTC timestamps

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

PaySim's `step` is a synthetic simulation step (commonly described as one hour), not a measured UTC timestamp (§5.1). The canonical transaction contract (§6.2) separates `event_time_raw`, `event_time_utc` (nullable, populated only where an actual clock timestamp and timezone semantics are defensible), `event_time_index` (the source's actual temporal representation, e.g. PaySim `step`), and a required `time_semantics` enum (`OBSERVED_CLOCK`, `SYNTHETIC_DATETIME`, `SYNTHETIC_STEP`, `UNKNOWN`). Deriving `event_time_utc` from `step` by assuming an arbitrary starting date would make synthetic step numbers look like real-world timestamps, violating the semantic-integrity principle (§3).

**Decision**

1. `step` is the synthetic time / split index; it is not a measured UTC timestamp (§5.1).
2. Do not generate `event_time_utc` by assuming an arbitrary starting date; any optional anchor is display-only, marked artificial, and never source-observed time (§5.1, §6.2).
3. `event_time_utc` is nullable and populated only where an actual clock timestamp and timezone semantics are defensible (§6.2).
4. `time_semantics` uses `SYNTHETIC_STEP` for PaySim (§6.2).
5. For point-in-time windows, use `history_time < current_step` as the conservative default; file order is not event order unless the source specification and audit demonstrate it (§9.2).

**Alternatives considered**

- Derive UTC timestamps from `step` with an assumed epoch: rejected; synthetic step numbers are not real-world timestamps and this violates semantic integrity (§3, §5.1, §6.2).
- Treat file order as event order within the same `step`: rejected; PaySim does not provide a trustworthy within-step event order (§9.2).

**Consequences and trade-offs**

- Honest, auditable time semantics with no fabricated wall-clock claims; results are tied to the synthetic `step` index.
- Loses wall-clock anchoring; any display anchor must be explicitly labelled artificial and cannot be used as evidence of real event time.

**Tests/evidence required**

- Source audit records `step` semantics, unique time values, and that `event_time_utc` is not fabricated from `step` (§5.1; §14.1 temporal/leakage tests).
- Temporal/leakage tests verify the current event is excluded from history and no future event affects a past feature (§14.1).

**Revisit trigger**

Revisit if a source with real clock timestamps is introduced or if source time semantics change.

