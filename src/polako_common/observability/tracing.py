"""OpenTelemetry tracing setup"""

import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.aiopg import AiopgInstrumentor

logger = logging.getLogger(__name__)

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(
    service_name: str,
    service_version: str = "1.0.0",
    otlp_endpoint: str = "http://localhost:4317",
    environment: str = "development"
) -> TracerProvider:
    """Setup OpenTelemetry tracing"""
    global _tracer_provider
    
    if _tracer_provider:
        return _tracer_provider
    
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": environment
    })
    
    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    
    # Create OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Create span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    _tracer_provider.add_span_processor(span_processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    
    # Auto-instrument common libraries
    FastAPIInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
    AiopgInstrumentor.instrument()
    
    logger.info(f"Tracing initialized for {service_name}")
    return _tracer_provider


def get_tracer(name: str) -> trace.Tracer:
    """Get tracer instance"""
    return trace.get_tracer(name)
