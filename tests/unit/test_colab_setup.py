# =============================================================================
# tests/test_colab_setup.py
# =============================================================================
"""
Comprehensive unit tests for the runtime environment utilities.

This module tests the detection of Google Colab, the environment snapshot
function, and the Colab environment setup logic, including path resolution
and graceful fallbacks.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from fraud_platform.common.colab_setup import (
    check_environment,
    is_colab,
    setup_colab_environment,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_colab_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the environment to simulate running inside Google Colab."""
    monkeypatch.setattr("fraud_platform.common.colab_setup.is_colab", lambda: True)


@pytest.fixture
def mock_local_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the environment to simulate running locally (not Colab)."""
    monkeypatch.setattr("fraud_platform.common.colab_setup.is_colab", lambda: False)


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    """Create a fake project structure with pyproject.toml and src directory."""
    project_root = tmp_path / "fraud-risk-platform"
    project_root.mkdir()
    (project_root / "pyproject.toml").touch()
    (project_root / "src").mkdir()
    return project_root


# =============================================================================
# Tests for is_colab()
# =============================================================================


class TestIsColab:
    """Test suite for the is_colab() detection function."""

    def test_is_colab_returns_false_outside_colab(self) -> None:
        """Verify that local test execution is not identified as Google Colab."""
        # In the local pytest environment, google.colab is not installed
        assert is_colab() is False

    def test_is_colab_returns_true_when_module_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that is_colab returns True when google.colab is importable."""
        import types

        # Create a fake google.colab module and inject it into sys.modules
        fake_google = types.ModuleType("google")
        fake_colab = types.ModuleType("google.colab")
        monkeypatch.setitem(sys.modules, "google", fake_google)
        monkeypatch.setitem(sys.modules, "google.colab", fake_colab)

        assert is_colab() is True


# =============================================================================
# Tests for check_environment()
# =============================================================================


class TestCheckEnvironment:
    """Test suite for the check_environment() snapshot function."""

    def test_check_environment_returns_expected_keys(self) -> None:
        """Verify that environment inspection returns all expected keys."""
        environment = check_environment()

        assert set(environment) == {
            "runtime",
            "python_version",
            "platform",
            "cwd",
            "project_root",
            "src_in_sys_path",
        }

    def test_check_environment_identifies_local_runtime(self) -> None:
        """Verify that the current test environment is identified as local."""
        environment = check_environment()
        assert environment["runtime"] == "local"

    def test_check_environment_identifies_colab_runtime(self, mock_colab_env: None) -> None:
        """Verify that the environment is identified as Colab when mocked."""
        environment = check_environment()
        assert environment["runtime"] == "colab"

    def test_check_environment_matches_current_python_version(self) -> None:
        """Verify that the reported Python version matches the running interpreter."""
        environment = check_environment()
        expected_version = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        assert environment["python_version"] == expected_version

    def test_check_environment_returns_non_empty_platform(self) -> None:
        """Verify that the runtime platform is reported."""
        environment = check_environment()
        assert environment["platform"]

    def test_check_environment_returns_non_empty_working_directory(self) -> None:
        """Verify that the current working directory is reported."""
        environment = check_environment()
        assert environment["cwd"]

    def test_check_environment_project_root_defaults_to_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that project_root is 'Not Set' when the env var is missing."""
        monkeypatch.delenv("FRAUD_PLATFORM_ROOT", raising=False)
        environment = check_environment()
        assert environment["project_root"] == "Not Set"
        assert environment["src_in_sys_path"] is False


# =============================================================================
# Tests for setup_colab_environment()
# =============================================================================


class TestSetupColabEnvironment:
    """Test suite for the setup_colab_environment() configuration logic."""

    def test_setup_does_nothing_when_not_in_colab(
        self, mock_local_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that setup_colab_environment is a no-op outside Colab."""
        initial_env = dict(os.environ)
        initial_path = list(sys.path)

        setup_colab_environment()

        assert dict(os.environ) == initial_env
        assert list(sys.path) == initial_path

    def test_setup_uses_env_var_if_set(
        self, mock_colab_env: None, fake_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that setup uses FRAUD_PLATFORM_ROOT when provided."""
        monkeypatch.setenv("FRAUD_PLATFORM_ROOT", str(fake_project))
        monkeypatch.setattr(sys, "path", list(sys.path))  # Isolate sys.path

        setup_colab_environment()

        assert os.environ["FRAUD_PLATFORM_ROOT"] == str(fake_project)
        assert str(fake_project / "src") in sys.path

    def test_setup_falls_back_to_default_colab_path(
        self,
        mock_colab_env: None,
        fake_project: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Verify that setup uses the default Colab path if env var is missing.

        To keep this test cross-platform (Windows/macOS/Linux), the default
        Colab path constant is monkeypatched to point at a real temporary
        directory created by the `fake_project` fixture.
        """
        monkeypatch.delenv("FRAUD_PLATFORM_ROOT", raising=False)
        monkeypatch.setattr(sys, "path", list(sys.path))

        # Point the default Colab path to our temp project instead of
        # the hard-coded /content/... path, which is not portable.
        monkeypatch.setattr(
            "fraud_platform.common.colab_setup._DEFAULT_COLAB_PROJECT_ROOT",
            str(fake_project),
        )

        setup_colab_environment()

        assert os.environ["FRAUD_PLATFORM_ROOT"] == str(fake_project)
        assert str(fake_project / "src") in sys.path

    def test_setup_searches_cwd_for_project_marker(
        self, mock_colab_env: None, fake_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that setup searches cwd and parents for pyproject.toml."""
        monkeypatch.delenv("FRAUD_PLATFORM_ROOT", raising=False)
        monkeypatch.setattr(sys, "path", list(sys.path))

        # Mock cwd to return the fake project root
        monkeypatch.setattr(Path, "cwd", lambda: fake_project)

        setup_colab_environment()

        assert os.environ["FRAUD_PLATFORM_ROOT"] == str(fake_project)
        assert str(fake_project / "src") in sys.path

    def test_setup_exits_gracefully_when_project_not_found(
        self, mock_colab_env: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that setup does nothing if pyproject.toml cannot be found."""
        monkeypatch.delenv("FRAUD_PLATFORM_ROOT", raising=False)
        initial_env = dict(os.environ)
        initial_path = list(sys.path)

        # Mock Path.is_file to always return False (no pyproject.toml anywhere)
        monkeypatch.setattr(Path, "is_file", lambda self: False)

        setup_colab_environment()

        # Environment and sys.path should remain unchanged
        assert dict(os.environ) == initial_env
        assert list(sys.path) == initial_path
