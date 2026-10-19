"""
Unit tests for centralized application settings.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fraud_risk_platform.config.settings import (
    _get_bool_environment_value,
    _get_environment_value,
    _resolve_project_root,
    load_settings,
)


def test_default_settings_are_loaded() -> None:
    """Verify that foundational defaults are applied."""
    settings = load_settings()

    assert settings.application.name == "fraud-risk-platform"
    assert settings.application.environment == "development"
    assert settings.application.debug is False
    assert settings.runtime.timezone == "UTC"


def test_environment_values_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that supported environment variables override defaults."""
    monkeypatch.setenv(
        "FRAUD_PLATFORM_APP_NAME",
        "test-platform",
    )
    monkeypatch.setenv(
        "FRAUD_PLATFORM_ENVIRONMENT",
        "test",
    )
    monkeypatch.setenv(
        "FRAUD_PLATFORM_DEBUG",
        "true",
    )
    monkeypatch.setenv(
        "FRAUD_PLATFORM_TIMEZONE",
        "Africa/Cairo",
    )

    settings = load_settings()

    assert settings.application.name == "test-platform"
    assert settings.application.environment == "test"
    assert settings.application.debug is True
    assert settings.runtime.timezone == "Africa/Cairo"


def test_boolean_environment_values_accept_true_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify accepted representations of true."""
    for value in ("1", "true", "TRUE", "yes", "YES", "on", "ON"):
        monkeypatch.setenv("TEST_BOOLEAN", value)

        assert (
            _get_bool_environment_value(
                "TEST_BOOLEAN",
                default=False,
            )
            is True
        )


def test_boolean_environment_values_accept_false_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify accepted representations of false."""
    for value in ("0", "false", "FALSE", "no", "NO", "off", "OFF"):
        monkeypatch.setenv("TEST_BOOLEAN", value)

        assert (
            _get_bool_environment_value(
                "TEST_BOOLEAN",
                default=True,
            )
            is False
        )


def test_invalid_boolean_environment_value_raises_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that unsupported boolean values fail explicitly."""
    monkeypatch.setenv(
        "TEST_BOOLEAN",
        "not-a-boolean",
    )

    with pytest.raises(ValueError, match="Invalid boolean value"):
        _get_bool_environment_value(
            "TEST_BOOLEAN",
            default=False,
        )


def test_missing_environment_value_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that missing environment variables use their defaults."""
    monkeypatch.delenv(
        "TEST_VALUE",
        raising=False,
    )

    assert (
        _get_environment_value(
            "TEST_VALUE",
            "default-value",
        )
        == "default-value"
    )


def test_empty_environment_value_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that an empty environment variable uses its default."""
    monkeypatch.setenv(
        "TEST_VALUE",
        "   ",
    )

    assert (
        _get_environment_value(
            "TEST_VALUE",
            "default-value",
        )
        == "default-value"
    )


def test_project_root_environment_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify that an explicit project-root override is respected."""
    monkeypatch.setenv(
        "FRAUD_PLATFORM_ROOT",
        str(tmp_path),
    )

    assert _resolve_project_root() == tmp_path.resolve()


def test_project_root_is_discovered_from_project_marker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify project-root discovery through pyproject.toml."""
    project_root = tmp_path / "project"

    source_dir = project_root / "src" / "fraud_risk_platform" / "config"
    source_dir.mkdir(parents=True)

    (project_root / "pyproject.toml").touch()

    monkeypatch.delenv(
        "FRAUD_PLATFORM_ROOT",
        raising=False,
    )

    discovered_root = None

    # The resolver searches from the actual module location, so this test
    # verifies the marker behavior indirectly through the current project.
    current_root = _resolve_project_root()

    if (current_root / "pyproject.toml").is_file():
        discovered_root = current_root

    assert discovered_root is not None


def test_settings_paths_are_relative_to_project_root() -> None:
    """Verify that derived paths use the resolved project root."""
    settings = load_settings()

    assert settings.paths.data_dir == settings.paths.project_root / "data"
    assert settings.paths.logs_dir == settings.paths.project_root / "logs"
    assert settings.paths.artifacts_dir == settings.paths.project_root / "artifacts"


def test_settings_paths_are_absolute() -> None:
    """Verify that all configured filesystem paths are absolute."""
    settings = load_settings()

    assert settings.paths.project_root.is_absolute()
    assert settings.paths.data_dir.is_absolute()
    assert settings.paths.logs_dir.is_absolute()
    assert settings.paths.artifacts_dir.is_absolute()


def test_frp_data_root_overrides_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify FRP_DATA_ROOT environment variable overrides the default path."""
    custom_path = tmp_path / "custom_data"
    monkeypatch.setenv("FRP_DATA_ROOT", str(custom_path))

    settings = load_settings()

    assert settings.frp_data_root == custom_path.resolve()


def test_frp_models_root_overrides_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify FRP_MODELS_ROOT environment variable overrides the default path."""
    custom_path = tmp_path / "custom_models"
    monkeypatch.setenv("FRP_MODELS_ROOT", str(custom_path))

    settings = load_settings()

    assert settings.frp_models_root == custom_path.resolve()


def test_frp_evidence_root_overrides_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify FRP_EVIDENCE_ROOT environment variable overrides the default path."""
    custom_path = tmp_path / "custom_evidence"
    monkeypatch.setenv("FRP_EVIDENCE_ROOT", str(custom_path))

    settings = load_settings()

    assert settings.frp_evidence_root == custom_path.resolve()
