# Fraud Risk Platform

Portfolio-grade engineering project for financial fraud detection.

## Status
Phase 0 — repository baseline established. No functional pipeline yet.

## Authoritative documents
- [Engineering baseline](docs/architecture/MASTER_ENGINEERING_PLAN.md) (v4.2.0; canonical unversioned copy, historical copy at `docs/architecture/MASTER_ENGINEERING_PLAN v4.2.0.md`)
- [Decision records](docs/decisions/)
- [Phase 0A inspection](docs/reports/phase0_inspection.md)

## Environment
- Primary: Google Colab + Google Drive (ADR-0012)
- Development: Windows + VS Code + `uv`
- Reviewer reproduction: Docker (Phase 7)

## IMPLEMENTED (verified by tests)
- Package skeleton (`fraud_risk_platform`): `uv run pytest` passes
- Configuration (`config/settings.py`): 11 tests
- Logging (`common/logging.py`): 11 tests
- Environment detection (`common/environment.py`): 14 tests
- Bootstrap (`colab_setup.py`, root): 3 tests
- Total: 39 passing tests

## PLANNED (not yet implemented)
Data ingestion, Bronze/Silver/Gold layers, feature engineering, ML pipeline,
policy simulation, FastAPI scoring API. See plan §15.

## Reproduce
```bash
git clone <repo>
cd fraud-risk-platform
uv sync
uv run pytest
```

