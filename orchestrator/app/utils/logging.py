"""Logging configuration and utilities."""

import logging
import sys
from typing import Any, Dict

from loguru import logger

from app.config import get_settings

settings = get_settings()


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward Loguru sinks.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Setup logging configuration using Loguru.
    """
    # Remove default logger
    logger.remove()

    # Add custom handler
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=settings.debug,
    )

    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    # Add file handler for all logs
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept uvicorn logs
    for _log in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]


def log_request(
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    user_id: int = None,
) -> None:
    """
    Log HTTP request.

    Args:
        method: HTTP method
        url: Request URL
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user ID
    """
    user_info = f"user_id={user_id}" if user_id else "anonymous"
    logger.info(
        f"{method} {url} - {status_code} - {duration_ms:.2f}ms - {user_info}"
    )


def log_deployment(
    deployment_id: int,
    status: str,
    message: str,
    **kwargs: Any,
) -> None:
    """
    Log deployment event.

    Args:
        deployment_id: Deployment ID
        status: Deployment status
        message: Log message
        **kwargs: Additional context
    """
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Deployment {deployment_id} [{status}]: {message} | {context}")


def log_error(
    error: Exception,
    context: Dict[str, Any] = None,
    user_id: int = None,
) -> None:
    """
    Log error with context.

    Args:
        error: Exception object
        context: Additional context dictionary
        user_id: Optional user ID
    """
    ctx = context or {}
    if user_id:
        ctx["user_id"] = user_id

    logger.exception(
        f"Error: {str(error)} | Context: {ctx}",
        exc_info=error,
    )


def log_security_event(
    event_type: str,
    user_id: int = None,
    ip_address: str = None,
    details: str = None,
) -> None:
    """
    Log security-related event.

    Args:
        event_type: Type of security event
        user_id: Optional user ID
        ip_address: Optional IP address
        details: Optional additional details
    """
    parts = [f"Security Event: {event_type}"]
    if user_id:
        parts.append(f"user_id={user_id}")
    if ip_address:
        parts.append(f"ip={ip_address}")
    if details:
        parts.append(f"details={details}")

    logger.warning(" | ".join(parts))


def log_integration_event(
    integration_type: str,
    event: str,
    success: bool,
    details: Dict[str, Any] = None,
) -> None:
    """
    Log integration event.

    Args:
        integration_type: Type of integration (WLED, FPP, etc.)
        event: Event description
        success: Whether event was successful
        details: Optional additional details
    """
    status = "SUCCESS" if success else "FAILED"
    details_str = " | ".join(f"{k}={v}" for k, v in (details or {}).items())

    if success:
        logger.info(f"Integration [{integration_type}] {event} - {status} | {details_str}")
    else:
        logger.error(f"Integration [{integration_type}] {event} - {status} | {details_str}")


# Export logger instance
__all__ = [
    "logger",
    "setup_logging",
    "log_request",
    "log_deployment",
    "log_error",
    "log_security_event",
    "log_integration_event",
]
