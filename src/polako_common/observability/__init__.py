"""Observability infrastructure with OpenTelemetry and Loguru"""

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

__all__ = [
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
