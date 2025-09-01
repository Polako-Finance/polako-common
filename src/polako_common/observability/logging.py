"""Structured logging setup with correlation IDs"""

import logging
import sys
from typing import Dict, Any, Optional
import structlog
from structlog.stdlib import LoggerFactory


def setup_structured_logging(
    service_name: str,
    log_level: str = "INFO",
    json_logs: bool = True
) -> None:
    """Setup structured logging with correlation ID support"""
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Add service name to all logs
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def __init__(self, correlation_id_getter: callable):
        super().__init__()
        self.correlation_id_getter = correlation_id_getter
    
    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = self.correlation_id_getter()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get structured logger instance"""
    return structlog.get_logger(name)
