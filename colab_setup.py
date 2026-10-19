#!/usr/bin/env python3
"""
colab_setup.py - Google Colab and Google Drive runtime bootstrap.

Per MASTER_ENGINEERING_PLAN.md §8.5.1 and ADR-0012 §5:
This bootstrap script runs at the repository root before dependencies are installed.
It uses only the Python standard library.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Final

DEFAULT_DRIVE_BASE: Final[str] = "/content/drive/MyDrive/fraud-risk-platform"


def is_colab() -> bool:
    """Return True if running inside Google Colab."""
    try:
        import google.colab  # noqa: F401

        return True
    except ImportError:
        return False


def mount_drive(mount_point: str = "/content/drive") -> None:
    """Mount Google Drive if running in Colab."""
    try:
        from google.colab import drive

        drive.mount(mount_point)
    except Exception as exc:
        raise RuntimeError(f"Failed to mount Google Drive at {mount_point}: {exc}") from exc


def ensure_uv() -> str:
    """Ensure uv package manager is installed and return its version."""
    uv_bin = shutil.which("uv")
    if not uv_bin:
        print("[colab_setup] 'uv' not found in PATH; installing via pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
            check=True,
        )
        uv_bin = shutil.which("uv")
        if not uv_bin:
            raise RuntimeError("Failed to install or locate 'uv' in PATH.")

    proc = subprocess.run(
        ["uv", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def run_uv_sync(project_root: Path) -> None:
    """Run `uv sync` from the repository root."""
    print(f"[colab_setup] Running 'uv sync' in {project_root}...")
    subprocess.run(
        ["uv", "sync"],
        cwd=str(project_root),
        check=True,
    )


def resolve_roots(base_dir: Path | None = None) -> dict[str, Path]:
    """
    Resolve and create persistent roots for data, models, and evidence.

    Reads FRP_DATA_ROOT, FRP_MODELS_ROOT, and FRP_EVIDENCE_ROOT from the
    environment if set; otherwise falls back to Drive defaults.
    Creates each directory and exports the resolved paths into os.environ.
    """
    base = base_dir if base_dir is not None else Path(DEFAULT_DRIVE_BASE)

    data_env = os.environ.get("FRP_DATA_ROOT")
    models_env = os.environ.get("FRP_MODELS_ROOT")
    evidence_env = os.environ.get("FRP_EVIDENCE_ROOT")

    roots = {
        "FRP_DATA_ROOT": Path(data_env) if data_env else base / "data",
        "FRP_MODELS_ROOT": Path(models_env) if models_env else base / "models",
        "FRP_EVIDENCE_ROOT": Path(evidence_env) if evidence_env else base / "docs" / "evidence",
    }

    for env_key, root_path in roots.items():
        root_path.mkdir(parents=True, exist_ok=True)
        os.environ[env_key] = str(root_path.resolve())

    return roots


resolve_and_create_roots = resolve_roots


def smoke_test_roundtrip(root: Path) -> None:
    """
    Perform a temporary write, fresh read-back, and SHA-256 check.

    Per §8.4 step 4: verification must use a fresh file open/stat, not the
    write handle.
    """
    test_file = root / f".smoke_test_{uuid.uuid4().hex}.tmp"
    payload = f"smoke_test_verification_{uuid.uuid4().hex}\n".encode("utf-8")
    expected_hash = hashlib.sha256(payload).hexdigest()

    try:
        with open(test_file, "wb") as f:
            f.write(payload)
            f.flush()

        with open(test_file, "rb") as f:
            read_payload = f.read()

        actual_hash = hashlib.sha256(read_payload).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(
                f"Smoke test hash mismatch at {root}: expected {expected_hash}, got {actual_hash}"
            )
    finally:
        if test_file.exists():
            test_file.unlink()


smoke_test_root = smoke_test_roundtrip


def main() -> int:
    """Bootstrap entry point."""
    if not is_colab():
        print("Not in Colab. Skipping Colab-specific bootstrap.")
        return 0

    print("[colab_setup] Colab environment detected. Starting bootstrap...")
    mount_drive("/content/drive")

    uv_version = ensure_uv()
    project_root = Path(__file__).resolve().parent
    run_uv_sync(project_root)

    roots = resolve_roots()
    for name, path in roots.items():
        smoke_test_roundtrip(path)

    print("==================================================================")
    print("Colab Bootstrap Completed Successfully")
    print(f"Python Version: {platform.python_version()}")
    print(f"uv Version:     {uv_version}")
    print(f"Workspace Root: {project_root} (ephemeral session VM)")
    for name, path in roots.items():
        print(f"{name:18}: {path}")
    print("WARNING: Session workspace is ephemeral; committed data must stay in Drive roots.")
    print("==================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())

