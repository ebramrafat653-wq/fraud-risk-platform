"""
Unit tests for centralized logging configuration.
"""

from __future__ import annotations

import logging

import pytest

from fraud_platform.common.logging import (
    get_logger,
    is_configured,
    setup_logging,
)


@pytest.fixture(autouse=True)
def reset_logging_state() -> None:
    """
    Reset logging configuration state before each test.

    The logging module owns process-wide state, so tests must not depend on
    configuration left behind by another test.
    """
    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    setup_module = __import__(
        "fraud_platform.common.logging",
        fromlist=["_configured"],
    )

    setup_module._configured = False


def test_get_logger_returns_named_logger() -> None:
    """Verify that get_logger returns the requested named logger."""
    logger = get_logger("fraud_platform.test")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "fraud_platform.test"


def test_get_logger_does_not_configure_logging() -> None:
    """Verify that obtaining a logger does not configure the root logger."""
    root_logger = logging.getLogger()

    handlers_before = list(root_logger.handlers)
    level_before = root_logger.level

    get_logger("fraud_platform.test")

    assert root_logger.handlers == handlers_before
    assert root_logger.level == level_before


def test_setup_logging_configures_root_logger() -> None:
    """Verify that setup_logging configures the application root logger."""
    setup_logging()

    root_logger = logging.getLogger()

    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0], logging.StreamHandler)


def test_setup_logging_marks_module_as_configured() -> None:
    """Verify that successful setup updates the module configuration state."""
    assert is_configured() is False

    setup_logging()

    assert is_configured() is True


def test_setup_logging_is_idempotent() -> None:
    """Verify that repeated setup calls do not duplicate handlers."""
    setup_logging()

    root_logger = logging.getLogger()
    first_handlers = list(root_logger.handlers)

    setup_logging()

    assert root_logger.handlers == first_handlers


def test_setup_logging_honors_custom_log_level() -> None:
    """Verify that a custom logging level is applied."""
    setup_logging(level=logging.DEBUG)

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG


def test_setup_logging_rejects_invalid_log_level() -> None:
    """Verify that non-integer logging levels are rejected."""
    with pytest.raises(TypeError):
        setup_logging(level="INFO")  # type: ignore[arg-type]


def test_setup_logging_rejects_boolean_log_level() -> None:
    """Verify that boolean values are rejected as logging levels."""
    with pytest.raises(TypeError):
        setup_logging(level=True)  # type: ignore[arg-type]


def test_setup_logging_supports_file_logging(tmp_path) -> None:
    """Verify that an optional file handler is created."""
    log_file = tmp_path / "logs" / "application.log"

    setup_logging(log_file=log_file)

    root_logger = logging.getLogger()

    assert len(root_logger.handlers) == 2
    assert log_file.parent.exists()

    logger = get_logger("fraud_platform.test")
    logger.info("test message")

    for handler in root_logger.handlers:
        handler.flush()

    assert log_file.exists()
    assert "test message" in log_file.read_text(encoding="utf-8")


def test_setup_logging_force_reconfigures_handlers() -> None:
    """Verify that force=True replaces existing root handlers."""
    setup_logging(level=logging.INFO)

    root_logger = logging.getLogger()
    first_handler = root_logger.handlers[0]

    setup_logging(
        level=logging.DEBUG,
        force=True,
    )

    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert root_logger.handlers[0] is not first_handler


def test_setup_logging_creates_missing_log_directory(tmp_path) -> None:
    """Verify that missing parent directories are created automatically."""
    log_file = tmp_path / "nested" / "logs" / "application.log"

    setup_logging(log_file=log_file)

    assert log_file.parent.exists()
    assert log_file.exists()
