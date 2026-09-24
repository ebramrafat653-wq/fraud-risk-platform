# =============================================================================
# src/fraud_platform/common/logging.py
# =============================================================================
"""
Centralized logging configuration for the Fraud & Risk Platform.

Design Goals
------------
- Single, predictable configuration point for the application.
- Console logging for local development, notebooks, containers, and CI.
- Optional file logging for batch workloads and long-running processes.
- Thread-safe initialization.
- No hidden configuration side effects.
- Explicit ownership of the application root logger at application boundaries.
- Clear behavior when running inside external environments such as
  Jupyter, Google Colab, or pytest.
- Standard-library only.

Architecture
------------
Application entry points are responsible for configuring logging:

    setup_logging()
        |
        +-- Root logger
              |
              +-- Console handler
              |
              +-- Optional file handler

Application modules only request named loggers:

    get_logger(__name__)

Modules must not configure the global logging system themselves.

Usage
-----
Application entry point:

    from fraud_platform.common.logging import get_logger, setup_logging

    setup_logging()
    logger = get_logger(__name__)
    logger.info("Application started")

Application module:

    from fraud_platform.common.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Processing transaction")

Ownership
---------
This module assumes that the Fraud & Risk Platform owns the root logger when
``setup_logging()`` is called at an application boundary.

The ``force`` parameter intentionally allows the application to replace
existing root handlers. This is useful when a host environment has already
installed logging handlers, but it must only be used where the application
explicitly owns the logging configuration.

The module does not attempt to manage logging configuration performed by
external applications after ``setup_logging()`` returns.
"""

from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================
import logging
import sys
import threading
from pathlib import Path
from typing import Final

# =============================================================================
# Module Constants
# =============================================================================
# These constants define the default logging format used by the platform.
#
# They remain private so other modules do not become coupled to the exact
# formatting contract. If the format changes in the future, only this module
# should normally need modification.
# =============================================================================

_DEFAULT_LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_DEFAULT_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# Module State
# =============================================================================
# Logging configuration is process-local state.
#
# The lock protects the configuration operation from concurrent initialization
# attempts. This is important because logging configuration modifies the
# process-wide root logger.
# =============================================================================

_configured: bool = False

_configure_lock: threading.Lock = threading.Lock()


# =============================================================================
# Public API
# =============================================================================


def setup_logging(
    level: int = logging.INFO,
    log_file: str | Path | None = None,
    force: bool = False,
) -> None:
    """
    Configure application-wide logging.

    This function owns the root logger configuration for the current
    application process and should be called explicitly at the application
    boundary.

    Typical application boundaries include:

    - CLI entry points
    - API startup
    - Worker bootstrap
    - Batch-job entry points
    - Notebook initialization

    Repeated calls are ignored after successful configuration unless
    ``force=True`` is explicitly requested.

    Parameters
    ----------
    level:
        Root logger level.

        Common values include:

        - ``logging.DEBUG``
        - ``logging.INFO``
        - ``logging.WARNING``
        - ``logging.ERROR``
        - ``logging.CRITICAL``

    log_file:
        Optional path for persistent file logging.

        Parent directories are created automatically when necessary.

        Examples:

            "logs/application.log"

            Path("logs/application.log")

    force:
        If ``True``, replace the existing root logger handlers with the
        handlers configured by this function.

        This is useful when the application explicitly needs to take
        ownership of logging configuration after an external environment
        has installed its own handlers.

        This should only be used at an application boundary and should not
        be called from reusable library modules.

    Raises
    ------
    TypeError
        If ``level`` is not an integer logging level.

    OSError
        If the parent directory for ``log_file`` cannot be created or the
        file cannot be opened for writing.

    Examples
    --------
    Basic console logging:

        >>> setup_logging()

    Debug logging:

        >>> setup_logging(level=logging.DEBUG)

    Console and file logging:

        >>> setup_logging(
        ...     level=logging.INFO,
        ...     log_file="logs/application.log",
        ... )

    Explicit reconfiguration:

        >>> setup_logging(
        ...     level=logging.DEBUG,
        ...     force=True,
        ... )
    """
    global _configured

    # -------------------------------------------------------------------------
    # Validate logging level
    # -------------------------------------------------------------------------
    # Python logging levels are represented by integers. Reject booleans even
    # though bool is technically a subclass of int in Python.
    # -------------------------------------------------------------------------

    if isinstance(level, bool) or not isinstance(level, int):
        raise TypeError(f"level must be an integer logging level, got {type(level).__name__}")

    # -------------------------------------------------------------------------
    # Configure the root logger atomically
    # -------------------------------------------------------------------------

    with _configure_lock:
        if _configured and not force:
            return

        formatter = logging.Formatter(
            fmt=_DEFAULT_LOG_FORMAT,
            datefmt=_DEFAULT_DATE_FORMAT,
        )

        handlers = _build_handlers(
            formatter=formatter,
            log_file=log_file,
        )

        # ``force=True`` intentionally gives the application ownership of the
        # root logger configuration at the application boundary.
        #
        # This replaces existing root handlers, which may have been installed
        # by environments such as Jupyter, Colab, pytest, or a host framework.
        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True,
        )

        _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger for an application module.

    This function never configures or mutates global logging state.

    Logging configuration is the responsibility of the application boundary.
    Individual modules should only obtain a named logger and emit log records.

    Parameters
    ----------
    name:
        Logger name, normally ``__name__`` from the calling module.

    Returns
    -------
    logging.Logger
        A standard-library logger instance.

    Examples
    --------
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing transaction")
    """
    return logging.getLogger(name)


def is_configured() -> bool:
    """
    Return whether this module has successfully configured logging.

    Notes
    -----
    The returned value represents the internal configuration state maintained
    by this module. It does not guarantee that another component has not
    modified the root logger after configuration.

    This function is intended for tests and diagnostics.

    Application code should not normally branch on this value. Logging
    configuration remains an explicit application-boundary responsibility.

    Returns
    -------
    bool
        ``True`` if ``setup_logging()`` has completed successfully through
        this module; otherwise ``False``.
    """
    return _configured


# =============================================================================
# Internal Helpers
# =============================================================================


def _build_handlers(
    formatter: logging.Formatter,
    log_file: str | Path | None,
) -> list[logging.Handler]:
    """
    Build the handlers used by the application root logger.

    A console handler is always created.

    A file handler is created only when ``log_file`` is explicitly provided.

    Parameters
    ----------
    formatter:
        Formatter applied consistently to every handler.

    log_file:
        Optional destination for persistent file logging.

    Returns
    -------
    list[logging.Handler]
        Configured console handler and, when requested, file handler.

    Raises
    ------
    OSError
        If the log directory cannot be created or the log file cannot be
        opened.
    """
    handlers: list[logging.Handler] = []

    # -------------------------------------------------------------------------
    # Console Handler
    # -------------------------------------------------------------------------
    # stdout keeps logs visible in local terminals, notebooks, containers,
    # and CI environments.
    # -------------------------------------------------------------------------

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    handlers.append(console_handler)

    # -------------------------------------------------------------------------
    # Optional File Handler
    # -------------------------------------------------------------------------

    if log_file is not None:
        log_path = Path(log_file)

        # ``Path(".")`` indicates that the file is located directly in the
        # current working directory and therefore requires no directory
        # creation.
        if log_path.parent != Path("."):
            log_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        file_handler = logging.FileHandler(
            filename=log_path,
            encoding="utf-8",
        )

        file_handler.setFormatter(formatter)

        handlers.append(file_handler)

    return handlers


# =============================================================================
# Public Module Interface
# =============================================================================

__all__ = [
    "get_logger",
    "is_configured",
    "setup_logging",
]
