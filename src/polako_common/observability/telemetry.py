"""
OpenTelemetry configuration and utilities for Polako Finance microservices.
"""

import os
from typing import Optional, Dict, Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.trace.span import format_trace_id, format_span_id

from loguru import logger


def setup_telemetry(
    service_name: str,
    namespace: str = "polako-finance",
    environment: str = "development",
    additional_attributes: Optional[Dict[str, Any]] = None,
) -> Optional[TracerProvider]:
    """
    Set up OpenTelemetry tracing for the service.

    Args:
        service_name: Name of the service
        namespace: Namespace of the service
        environment: Deployment environment (development, staging, production)
        additional_attributes: Additional resource attributes to include

    Returns:
        The configured TracerProvider or None if telemetry is disabled
    """
    # Only set up if OTEL_EXPORTER_OTLP_ENDPOINT is defined
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        logger.info(
            "OpenTelemetry exporter endpoint not defined, skipping telemetry setup"
        )
        return None

    # Prepare resource attributes
    resource_attributes = {
        SERVICE_NAME: service_name,
        "service.namespace": namespace,
        "deployment.environment": environment,
    }

    # Add additional attributes if provided
    if additional_attributes:
        resource_attributes.update(additional_attributes)

    # Create a resource with service information
    resource = Resource.create(resource_attributes)

    # Set up the tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Set up the OTLP exporter
    otlp_exporter = OTLPSpanExporter()
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)

    logger.info("OpenTelemetry tracer configured successfully")


def instrument_fastapi(app):
    """
    Instrument a FastAPI application for tracing.

    Args:
        app: The FastAPI application to instrument
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.debug("FastAPI instrumented for tracing")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def instrument_sqlalchemy():
    """
    Instrument SQLAlchemy for tracing.
    """
    try:
        # Check if already instrumented
        if not getattr(SQLAlchemyInstrumentor, "_is_instrumented", False):
            SQLAlchemyInstrumentor().instrument()
            SQLAlchemyInstrumentor._is_instrumented = True
        logger.debug("SQLAlchemy instrumented for tracing")
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}")


def instrument_aiohttp():
    """
    Instrument aiohttp client for tracing.
    """
    try:
        # Check if already instrumented
        if not getattr(AioHttpClientInstrumentor, "_is_instrumented", False):
            AioHttpClientInstrumentor().instrument()
            AioHttpClientInstrumentor._is_instrumented = True
        logger.debug("AioHTTP client instrumented for tracing")
    except Exception as e:
        logger.error(f"Failed to instrument aiohttp: {e}")


def get_trace_context() -> Dict[str, str]:
    """

    Returns:
        Dictionary with trace_id and span_id if available, empty dict otherwise
    """
    context = {}
    current_span = trace.get_current_span()
    if current_span:
        span_context = current_span.get_span_context()
        if span_context.is_valid:
            context["trace_id"] = format_trace_id(span_context.trace_id)
            context["span_id"] = format_span_id(span_context.span_id)
    return context
