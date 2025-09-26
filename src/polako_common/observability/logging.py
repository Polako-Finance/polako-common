"""Structured logging setup with Loguru and OpenTelemetry integration"""

import json
import logging
import sys
from typing import Dict, Any, Optional, Union, cast

from loguru import logger
from opentelemetry import trace
from opentelemetry.trace.span import format_trace_id, format_span_id


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and redirect them to Loguru.
    This allows libraries that use standard logging to use Loguru instead.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def add_trace_context(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add OpenTelemetry trace context to log records.
    This allows logs to be correlated with traces.
    """
    current_span = trace.get_current_span()
    if current_span:
        context = current_span.get_span_context()
        if context.is_valid:
            record["trace_id"] = format_trace_id(context.trace_id)
            record["span_id"] = format_span_id(context.span_id)
    return record


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    json_format: bool = False,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Configure Loguru for the application.

    Args:
        service_name: Name of the service for log identification
        log_level: Minimum log level to output
        json_format: Whether to output logs in JSON format
        correlation_id: Optional correlation ID to include in all logs
    """
    # Remove default handler
    logger.remove()

    # Prepare log format
    log_format = {
        "time": "{time:YYYY-MM-DD HH:mm:ss.SSS}",
        "level": "{level}",
        "message": "{message}",
        "service": service_name,
        "module": "{module}",
        "function": "{function}",
        "line": "{line}",
    }

    if correlation_id:
        log_format["correlation_id"] = correlation_id

    # Configure JSON serializer if needed
    if json_format:

        def serialize(record: Dict[str, Any]) -> str:
            subset = {
                "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "level": record["level"].name,
                "message": record["message"],
                "service": service_name,
                "module": record["module"],
                "function": record["function"],
                "line": record["line"],
            }

            # Add trace context
            subset = add_trace_context(subset)

            # Add correlation ID if available
            if correlation_id:
                subset["correlation_id"] = correlation_id

            # Add exception info if present
            if record["exception"]:
                subset["exception"] = record["exception"]

            # Add extra attributes
            if record.get("extra"):
                for key, value in record["extra"].items():
                    subset[key] = value

            return json.dumps(subset)

        logger.add(
            sys.stdout,
            level=log_level.upper(),
            format="{message}",
            serialize=serialize,
        )
    else:
        # For development: colorful console output
        logger.add(
            sys.stdout,
            level=log_level.upper(),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message} | {extra}",
        )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Replace standard library logger with Loguru
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Set Loguru as the root logger
    logging.root.handlers = [InterceptHandler()]

    logger.info(f"Logging configured for {service_name} at level {log_level}")
