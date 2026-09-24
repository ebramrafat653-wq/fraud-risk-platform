# =============================================================================
# src/fraud_platform/config/settings.py
# =============================================================================
"""
Centralized application configuration for the Fraud & Risk Platform.

Design Goals
------------
- Provide one explicit source for application configuration.
- Keep configuration independent from infrastructure-specific technologies.
- Avoid hard-coded machine-specific paths.
- Keep secrets and credentials outside the source code.
- Provide deterministic defaults for local development and CI.
- Support local development, notebooks, containers, and CI environments.
- Keep the configuration layer lightweight during the project foundation phase.

Architecture
------------
This module intentionally contains only foundational configuration.

Current configuration domains:
    Application
        - application name
        - environment
        - debug mode

    Runtime
        - timezone

    Paths
        - project root
        - data directory
        - logs directory
        - artifacts directory

Infrastructure-specific configuration such as PostgreSQL, Kafka, Redis,
MLflow, cloud storage, and external service credentials will be introduced
only after the data audit and workload analysis establish a concrete need.

Secrets
-------
Secrets and credentials must never be stored in this module.

Examples of values that do NOT belong here:
    - database passwords
    - API keys
    - access tokens
    - cloud credentials
    - private keys

Those values should be supplied through environment variables or an
appropriate secrets-management mechanism when the relevant infrastructure
is introduced.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# =============================================================================
# Constants
# =============================================================================

_PROJECT_MARKER: Final[str] = "pyproject.toml"

_DEFAULT_APP_NAME: Final[str] = "fraud-risk-platform"
_DEFAULT_ENVIRONMENT: Final[str] = "development"
_DEFAULT_TIMEZONE: Final[str] = "UTC"


# =============================================================================
# Project Root Resolution
# =============================================================================


def _resolve_project_root() -> Path:
    """
    Resolve the project root directory.

    Resolution order
    ----------------
    1. ``FRAUD_PLATFORM_ROOT`` environment variable.
    2. Search parent directories of this source file for ``pyproject.toml``.
    3. Fall back to the current working directory.

    The environment-variable override provides an explicit mechanism for
    installed packages, containers, or non-standard execution environments
    where the source file location does not represent the project root.

    The ``pyproject.toml`` search provides a structure-aware solution during
    local development without relying on a fixed directory depth.

    The current working directory is used only as a final fallback because
    an installed Python package does not inherently have knowledge of the
    application's project root.
    """
    configured_root = os.getenv("FRAUD_PLATFORM_ROOT")

    if configured_root and configured_root.strip():
        return Path(configured_root).expanduser().resolve()

    source_path = Path(__file__).resolve()

    for candidate in (source_path, *source_path.parents):
        if (candidate / _PROJECT_MARKER).is_file():
            return candidate

    return Path.cwd().resolve()


# =============================================================================
# Configuration Models
# =============================================================================


@dataclass(frozen=True, slots=True)
class ApplicationSettings:
    """
    Application-level configuration.

    Attributes
    ----------
    name:
        Logical name of the application.

    environment:
        Runtime environment, such as ``development``, ``test``, or
        ``production``.

    debug:
        Whether application debug behavior is enabled.

        This setting represents application-level debug intent. Individual
        subsystems should not assume that it automatically changes their
        behavior unless explicitly designed to consume it.
    """

    name: str
    environment: str
    debug: bool


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """
    Runtime-level configuration.

    Attributes
    ----------
    timezone:
        Canonical timezone used by the platform.

        The platform uses UTC as the internal canonical timezone to avoid
        ambiguity across local machines, containers, cloud environments,
        and distributed processing systems.
    """

    timezone: str


@dataclass(frozen=True, slots=True)
class PathSettings:
    """
    Filesystem paths used by the platform.

    Paths are derived from the resolved project root and are therefore not
    tied to a specific user's machine.
    """

    project_root: Path
    data_dir: Path
    logs_dir: Path
    artifacts_dir: Path


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Root configuration object for the Fraud & Risk Platform.

    Configuration is grouped by responsibility rather than exposed as one
    large flat collection of unrelated variables.
    """

    application: ApplicationSettings
    runtime: RuntimeSettings
    paths: PathSettings


# =============================================================================
# Environment Parsing
# =============================================================================


def _get_environment_value(
    name: str,
    default: str,
) -> str:
    """
    Read a string configuration value from the environment.

    Empty environment variables are treated as unset and therefore fall back
    to the provided default.
    """
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    return value.strip()


def _get_bool_environment_value(
    name: str,
    default: bool,
) -> bool:
    """
    Read a boolean configuration value from the environment.

    Accepted true values:
        ``1``, ``true``, ``yes``, ``on``

    Accepted false values:
        ``0``, ``false``, ``no``, ``off``

    Raises
    ------
    ValueError
        If the environment variable contains an unsupported value.
    """
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"Invalid boolean value for {name!r}: {value!r}. "
        "Expected one of: 1, 0, true, false, yes, no, on, off."
    )


# =============================================================================
# Settings Construction
# =============================================================================


def load_settings() -> Settings:
    """
    Build application settings from defaults and environment variables.

    Environment variables currently supported:
        FRAUD_PLATFORM_ROOT
        FRAUD_PLATFORM_APP_NAME
        FRAUD_PLATFORM_ENVIRONMENT
        FRAUD_PLATFORM_DEBUG
        FRAUD_PLATFORM_TIMEZONE

    Path directories are derived from the resolved project root rather than
    independently configured to avoid inconsistent filesystem layouts.
    """
    project_root = _resolve_project_root()

    application = ApplicationSettings(
        name=_get_environment_value(
            "FRAUD_PLATFORM_APP_NAME",
            _DEFAULT_APP_NAME,
        ),
        environment=_get_environment_value(
            "FRAUD_PLATFORM_ENVIRONMENT",
            _DEFAULT_ENVIRONMENT,
        ),
        debug=_get_bool_environment_value(
            "FRAUD_PLATFORM_DEBUG",
            default=False,
        ),
    )

    runtime = RuntimeSettings(
        timezone=_get_environment_value(
            "FRAUD_PLATFORM_TIMEZONE",
            _DEFAULT_TIMEZONE,
        ),
    )

    paths = PathSettings(
        project_root=project_root,
        data_dir=project_root / "data",
        logs_dir=project_root / "logs",
        artifacts_dir=project_root / "artifacts",
    )

    return Settings(
        application=application,
        runtime=runtime,
        paths=paths,
    )


# =============================================================================
# Default Application Settings
# =============================================================================

settings: Final[Settings] = load_settings()


__all__ = [
    "ApplicationSettings",
    "PathSettings",
    "RuntimeSettings",
    "Settings",
    "load_settings",
    "settings",
]
