"""Observability infrastructure with OpenTelemetry and Loguru"""

# Legacy imports for backward compatibility
from polako_common.observability.tracing import setup_tracing, get_tracer
from polako_common.observability.metrics import setup_metrics, get_meter

# New imports for enhanced observability
from polako_common.observability.telemetry import (
    setup_telemetry,
    instrument_fastapi,
    instrument_sqlalchemy,
    instrument_aiohttp,
    get_trace_context,
)
from polako_common.observability.logging import (
    setup_logging,
    InterceptHandler,
    add_trace_context,
)
from polako_common.observability.middleware import CorrelationIDMiddleware

# Legacy middleware
from polako_common.observability.middleware import TracingMiddleware, MetricsMiddleware

__all__ = [
    # Legacy exports
    "setup_tracing",
    "get_tracer",
    "setup_metrics",
    "get_meter",
    "setup_structured_logging",  # Kept for backward compatibility
    "TracingMiddleware",
    "MetricsMiddleware",
    # New exports
    "setup_telemetry",
    "instrument_fastapi",
    "instrument_sqlalchemy",
    "instrument_aiohttp",
    "get_trace_context",
    "setup_logging",
    "InterceptHandler",
    "add_trace_context",
    "CorrelationIDMiddleware",
]
