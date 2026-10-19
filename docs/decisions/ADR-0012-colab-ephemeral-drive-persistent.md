### ADR-0012: Execution Environment — Colab Ephemeral Compute with Persistent Google Drive Storage

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

The primary development and execution environment is Google Colab with Google Drive mounted for persistence. The Colab session disk is ephemeral and is lost when the runtime is disconnected or reset. The mounted Drive filesystem is a FUSE/API-backed virtual filesystem and must not be assumed to provide all native POSIX guarantees for rename, `flock`/`fcntl`, directory sync, latency, or concurrent updates. Drive-backed I/O can include mount/network/API overhead and can be rate-limited. These differences materially affect publication, recovery, and benchmark interpretation.

**Decision**

1. **Separate compute from persistence.** The Git clone, `.venv`, temporary downloads, active staging directories, and scratch processing files live on the current Colab session disk. Approved raw datasets, committed data products (`data/bronze`, `data/silver`, `data/gold`), model releases (`models/releases`), active pointers, and required evidence/tracking data live under mounted Drive roots.
2. **Use configurable logical roots.** `FRP_DATA_ROOT`, `FRP_MODELS_ROOT`, and `FRP_EVIDENCE_ROOT` resolve logical project roots to Drive-backed locations. Persisted manifests and pointers use paths relative to the declared logical root; do not store machine-specific absolute paths. Use explicit path configuration as the default; symlinks are optional only if tested in the target runtime.
3. **Adjust publication semantics in Section 8.** Build and validate outputs on the ephemeral session disk first, copy them into a new immutable run/release path on Drive, read back and verify their sizes/hashes, write and verify the immutable manifest, and update the relevant `current.json` only after the target is complete. The final pointer update is a *logical activation step*, not a promise of physical atomic rename on Drive. Readers must validate the pointer, target manifest, and required hashes and fail closed on invalid/missing data. A crash during pointer replacement may temporarily make the pointer unavailable or invalid; the design prioritizes rejecting an unverified target over guaranteeing uninterrupted availability.
4. **Single writer; marker is not a distributed lock.** Only one active publisher may write to the data/model roots at a time. A marker file containing a run ID, owner/session label, UTC timestamp, and available process metadata is an operational warning against accidental duplicate work. It is not considered a race-free lock across Colab sessions; the operating rule is the actual concurrency guard. Stale markers require operator verification before removal.
5. **Require `colab_setup.py`.** The bootstrap mounts Drive, installs/locates `uv`, runs `uv sync` from the cloned repository, configures and validates the persistent roots, and runs a small write/read-back/hash smoke test. It must be idempotent and must not delete existing data, model releases, or evidence.
6. **Benchmark storage location explicitly.** Every Phase 1 runtime/I/O benchmark records whether input was read directly from the Drive mount or copied to the ephemeral session disk first. These are distinct benchmark conditions and cannot be silently combined.
7. **Preserve environment reproducibility through Git and lockfiles.** `pyproject.toml` and `uv.lock` are source-controlled and restored by cloning the repository. The virtual environment is recreated per session and is not stored on Drive. MLflow runs and acceptance evidence that must survive session resets are configured to persistent Drive-backed roots; otherwise they must be labelled ephemeral.

**Alternatives considered**

- **Run everything on the ephemeral Colab disk:** rejected as the only storage strategy because datasets and committed artifacts would disappear with the session.
- **Run all active processing directly on Drive:** rejected as the default for heavy processing because of latency and filesystem semantic differences; small operations may still run there where measured and acceptable.
- **Move immediately to a dedicated VM or other cloud service:** deferred because no measured bottleneck currently justifies the cost and operational complexity.
- **Treat a Drive `*.lock` marker as a robust distributed lock:** rejected because check-then-create and stale-lock handling on the mounted filesystem are not sufficient to guarantee mutual exclusion.
- **Claim fully atomic pointer replacement on Drive:** rejected because the relevant semantics must not be assumed. If strong atomic activation or high availability becomes a requirement, use a storage primitive with documented conditional-update semantics or a tested native POSIX environment.

**Consequences and trade-offs**

The project incurs explicit path configuration and a bootstrap step. Drive-backed I/O may be slower than local disk and may temporarily make a pointer invalid/unavailable during a failed update. Immutable run directories, read-back hash verification, fail-closed readers, a single-writer operating rule, and retained prior releases reduce silent corruption risk but do not provide a general-purpose distributed transaction or lock manager.

**Tests/evidence required**

- Run `colab_setup.py` from a fresh Colab runtime; verify Drive is mounted, `uv` is available, `uv sync` succeeds, and logical roots resolve to the intended persistent locations.
- Write a small dummy output to Drive, read it back, and verify byte size and SHA-256.
- Simulate a crash/failure before manifest publication and during pointer update. Prove that no incomplete target is accepted; a reader must either continue using a verified prior pointer or fail closed.
- Test that a run-level `REJECT` never becomes the target of `current.json`.
- Record one Phase 1 I/O measurement with the source on the Drive mount and, if measured, a separate one with the verified copy on ephemeral disk.
- Document that the marker file is advisory and that concurrent writers are prohibited by the operating procedure.

**Revisit trigger**

Revisit this decision if reliable multi-writer publication, atomic pointer swaps, high availability during promotion, or performance requirements exceed what Colab plus Drive can support. Migrate only after a measured or contractually required limitation justifies the added platform complexity.

