# =============================================================================
# src/fraud_platform/common/colab_setup.py
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
    2. Adds the `src` directory to `sys.path` so `fraud_platform` can be
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
    project_root_str = os.getenv("FRAUD_PLATFORM_ROOT")

    if project_root_str and project_root_str.strip():
        project_root = Path(project_root_str).expanduser().resolve()
    else:
        # Fallback to the default Colab project path
        project_root = Path(_DEFAULT_COLAB_PROJECT_ROOT).resolve()

    # Verify the project root actually exists and contains the marker file
    if not (project_root / _PROJECT_MARKER).is_file():
        # If the default path doesn't work, try to find it from cwd
        cwd = Path.cwd().resolve()
        for candidate in (cwd, *cwd.parents):
            if (candidate / _PROJECT_MARKER).is_file():
                project_root = candidate
                break
        else:
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


def check_environment() -> dict[str, str | bool]:
    """
    Return a snapshot of the current runtime environment.

    This is useful for debugging, logging, and ensuring that the
    correct paths and environment variables are set.
    """
    project_root = os.getenv("FRAUD_PLATFORM_ROOT", "Not Set")
    src_path = str(Path(project_root) / "src") if project_root != "Not Set" else "Not Set"

    return {
        "runtime": "colab" if is_colab() else "local",
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "cwd": os.getcwd(),
        "project_root": project_root,
        "src_in_sys_path": src_path in sys.path,
    }


# =============================================================================
# Public Module Interface
# =============================================================================

__all__ = [
    "check_environment",
    "is_colab",
    "setup_colab_environment",
]
