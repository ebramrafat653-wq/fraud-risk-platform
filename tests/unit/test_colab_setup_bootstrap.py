"""
Unit tests for the root colab_setup.py bootstrap script.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is importable for root script tests
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import colab_setup


import pytest


def test_is_colab_false_locally() -> None:
    """Verify is_colab returns False in local test environment."""
    assert colab_setup.is_colab() is False


def test_resolve_roots_creates_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify resolve_roots creates the three required logical root directories."""
    for k in ("FRP_DATA_ROOT", "FRP_MODELS_ROOT", "FRP_EVIDENCE_ROOT"):
        monkeypatch.setenv(k, "")

    roots = colab_setup.resolve_roots(base_dir=tmp_path)

    assert set(roots.keys()) == {
        "FRP_DATA_ROOT",
        "FRP_MODELS_ROOT",
        "FRP_EVIDENCE_ROOT",
    }
    for path in roots.values():
        assert path.is_dir()

    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "models").is_dir()
    assert (tmp_path / "docs" / "evidence").is_dir()


def test_smoke_test_roundtrip(tmp_path: Path) -> None:
    """Verify smoke_test_roundtrip writes, reads back, hashes, and cleans up without exception."""
    test_dir = tmp_path / "smoke_target"
    test_dir.mkdir()

    colab_setup.smoke_test_roundtrip(test_dir)

    # Ensure temp file was cleaned up
    remaining = list(test_dir.iterdir())
    assert len(remaining) == 0

