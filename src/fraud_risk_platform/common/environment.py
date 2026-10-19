# =============================================================================
# src/fraud_risk_platform/common/environment.py
# =============================================================================
"""
Google Colab and runtime environment integration.

Design Goals
------------
- Detect whether the code is running inside Google Colab.
- Automatically configure the environment for Colab when detected.
- Ensure the project's `src` directory is importable.
- Set the `FRAUD_PLATFORM_ROOT` environment variable if needed.
- Provide a clean snapshot of the current runtime environment.
- Keep the module lightweight and dependency-free (standard library only).
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Final

# =============================================================================
# Constants
# =============================================================================

_DEFAULT_COLAB_PROJECT_ROOT: Final[str] = "/content/fraud-risk-platform"
_PROJECT_MARKER: Final[str] = "pyproject.toml"


# =============================================================================
# Environment Detection
# =============================================================================


def is_colab() -> bool:
    """
    Return True if running inside Google Colab.

    This function attempts to import the `google.colab` module, which is
    only available in the Colab runtime environment.
    """
    try:
        import google.colab  # noqa: F401

        return True
    except ImportError:
        return False


# =============================================================================
# Colab Environment Setup
# =============================================================================


def setup_colab_environment() -> None:
    """
    Configure the runtime environment for Google Colab.

    This function performs the following steps if running in Colab:
    1. Resolves the project root (either from an environment variable or
       a default Colab path).
    2. Adds the `src` directory to `sys.path` so `fraud_risk_platform` can be
       imported without installing the package.
    3. Sets the `FRAUD_PLATFORM_ROOT` environment variable so that
       `settings.py` resolves paths correctly.

    If not running in Colab, this function does nothing.
    """
    if not is_colab():
        return

    # -------------------------------------------------------------------------
    # Resolve Project Root
    # -------------------------------------------------------------------------
    frp_data_root_str = os.getenv("FRP_DATA_ROOT")
    fraud_platform_root_str = os.getenv("FRAUD_PLATFORM_ROOT")

    project_root: Path | None = None

    # 1. First check FRP_DATA_ROOT
    if frp_data_root_str and frp_data_root_str.strip():
        data_path = Path(frp_data_root_str.strip()).expanduser().resolve()
        candidate = data_path.parent if data_path.name == "data" else data_path
        if (candidate / _PROJECT_MARKER).is_file():
            project_root = candidate
        elif (data_path / _PROJECT_MARKER).is_file():
            project_root = data_path

    # 2. Then check FRAUD_PLATFORM_ROOT (deprecated fallback, print a warning)
    if project_root is None and fraud_platform_root_str and fraud_platform_root_str.strip():
        import warnings

        warnings.warn(
            "FRAUD_PLATFORM_ROOT is deprecated; use FRP_* roots instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        print("Warning: FRAUD_PLATFORM_ROOT is deprecated; use FRP_* roots instead.")
        candidate = Path(fraud_platform_root_str.strip()).expanduser().resolve()
        if (candidate / _PROJECT_MARKER).is_file():
            project_root = candidate

    # 3. Otherwise: fallback to default Colab path, cwd, or derive from __file__
    if project_root is None:
        default_colab_path = Path(_DEFAULT_COLAB_PROJECT_ROOT).resolve()
        if (default_colab_path / _PROJECT_MARKER).is_file():
            project_root = default_colab_path
        else:
            # Check cwd and parents first
            cwd = Path.cwd().resolve()
            for candidate in (cwd, *cwd.parents):
                if (candidate / _PROJECT_MARKER).is_file():
                    project_root = candidate
                    break
            else:
                # Derive from __file__ (walk up to find pyproject.toml)
                source_path = Path(__file__).resolve()
                for candidate in (source_path, *source_path.parents):
                    if (candidate / _PROJECT_MARKER).is_file():
                        project_root = candidate
                        break

    # Verify the project root actually exists and contains the marker file
    if project_root is None or not (project_root / _PROJECT_MARKER).is_file():
        # Cannot find project root; exit gracefully without changing state
        return

    # -------------------------------------------------------------------------
    # Configure Environment
    # -------------------------------------------------------------------------
    os.environ["FRAUD_PLATFORM_ROOT"] = str(project_root)

    src_path = project_root / "src"
    if src_path.is_dir() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


# =============================================================================
# Environment Snapshot
# =============================================================================


class EnvironmentSnapshot(dict[str, str | bool]):
    """Environment dictionary with case-insensitive key lookup for FRP_* variables."""

    def __getitem__(self, key: str) -> str | bool:
        if key in self:
            return super().__getitem__(key)
        lower_key = key.lower()
        if lower_key in self:
            return super().__getitem__(lower_key)
        upper_key = key.upper()
        if upper_key in self:
            return super().__getitem__(upper_key)
        return super().__getitem__(key)

    def get(self, key: str, default: str | bool | None = None) -> str | bool | None:
        try:
            return self[key]
        except KeyError:
            return default


def check_environment() -> dict[str, str | bool]:
    """
    Return a snapshot of the current runtime environment.

    This is useful for debugging, logging, and ensuring that the
    correct paths and environment variables are set.
    """
    project_root = os.getenv("FRAUD_PLATFORM_ROOT", "Not Set")
    src_path = str(Path(project_root) / "src") if project_root != "Not Set" else "Not Set"

    return EnvironmentSnapshot(
        {
            "runtime": "colab" if is_colab() else "local",
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "cwd": os.getcwd(),
            "project_root": project_root,
            "src_in_sys_path": src_path in sys.path,
            "frp_data_root": os.getenv("FRP_DATA_ROOT", "Not Set"),
            "frp_models_root": os.getenv("FRP_MODELS_ROOT", "Not Set"),
            "frp_evidence_root": os.getenv("FRP_EVIDENCE_ROOT", "Not Set"),
        }
    )


# =============================================================================
# Public Module Interface
# =============================================================================

__all__ = [
    "check_environment",
    "is_colab",
    "setup_colab_environment",
]
