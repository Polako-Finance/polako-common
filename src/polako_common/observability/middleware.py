"""
FastAPI middleware for observability.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from opentelemetry import trace


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to requests and responses.

    This middleware:
    1. Extracts correlation ID from request headers or generates a new one from trace ID
    2. Adds correlation ID to request state
    3. Adds correlation ID to Loguru context for structured logging
    4. Adds correlation ID to response headers
    """

    def __init__(self, app, header_name: str = "X-Correlation-ID"):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI application
            header_name: The name of the header to use for correlation ID
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and add correlation ID.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response
        """
        # Get correlation ID from header or generate a new one from trace ID
        correlation_id = request.headers.get(self.header_name) or str(
            trace.get_current_span().get_span_context().trace_id
        )

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id

        # Add correlation ID to Loguru context
        with logger.contextualize(correlation_id=correlation_id):
            # Log the request
            logger.debug(
                "Incoming request",
                path=request.url.path,
                method=request.method,
                client=request.client.host if request.client else "unknown",
            )

            # Process the request
            response = await call_next(request)

            # Log the response
            logger.debug(
                "Request completed",
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
            )

        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id

        return response
