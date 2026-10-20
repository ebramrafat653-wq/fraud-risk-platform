# ADR-0007: Local-first core stack; distributed technologies remain optional

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

The core dependency rule requires the ingestion and training path to run without Kafka, Redis, Airflow, Spark, or a hosted service (§4.3). §4.2 selects the core technology stack (Python with `uv`, Parquet, DuckDB, Pydantic, pytest, FastAPI, Docker packaging). §2.3's guardrail against overengineering states a technology is added only when a concrete requirement cannot be met, a reproducible benchmark shows a meaningful limitation, an extension has a defined objective, or it replaces an identified bottleneck. Colab with Drive is the primary environment through Phase 6; Docker (Phase 7) is a packaging/verification target, not a second implementation of Colab/Drive storage semantics (§4.3, §4.4).

**Decision**

1. Core stack is local-first: Python with `uv`, Parquet storage, DuckDB local analytics, Pydantic column contracts, pytest, and a FastAPI scoring endpoint (§4.2).
2. No Kafka, Redis, Airflow, Spark, or hosted service in the first release (§4.3 core dependency rule; §2 out of scope).
3. Distributed technologies remain optional and are added only on a measured requirement or benchmark (§2.3).
4. Colab + Drive is the primary environment through Phase 6; Docker (Phase 7) packages the stable local service for portable execution and CI verification (§4.3, §4.4).

**Alternatives considered**

- Distributed stack (Spark/Kafka) from the start: rejected; no measured bottleneck justifies the added cost and operational complexity (§2.3, §4.3).
- Treating Docker/CI as a second implementation of Colab/Drive storage semantics: rejected; Docker is a packaging and verification target, not a reimplementation (§4.4).

**Consequences and trade-offs**

- Simple, reproducible local stack with fast iteration; distributed scaling is deferred until justified by evidence.
- Some distributed patterns (exactly-once, concurrent writers) are not supported in the core release and require a future decision if needed.

**Tests/evidence required**

- Environment tests run `colab_setup.py` in a fresh Colab session and assert Drive roots are writable, `uv sync` uses the lockfile, and write/read-back/hash succeeds (§14.1; §8.5.1).
- CI runs local/fixture unit, contract, data, temporal/leakage, reproducibility, failure, integration, and regression tests (§4.4).

**Revisit trigger**

Revisit when a reproducible benchmark shows a meaningful limitation or a concrete requirement cannot be met by the local stack (§2.3).

