"""FastAPI Correlation ID and Prometheus request metrics middleware."""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from openquant.adapters.observability.telemetry import set_correlation_id
from openquant.adapters.observability.prometheus_metrics import metrics


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware for injecting correlation ID and recording Prometheus HTTP metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Extract or generate Correlation ID
        cid = request.headers.get("X-Correlation-ID")
        if not cid:
            cid = f"cid_{uuid.uuid4().hex[:12]}"
        set_correlation_id(cid)

        # 2. Timing
        start_time = time.perf_counter()
        method = request.method
        endpoint = request.url.path

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            status_code = str(response.status_code)

            # Record Prometheus Metrics (skip raw /metrics polling to prevent metric pollution)
            if endpoint != "/metrics":
                metrics.http_requests_total.inc(method=method, endpoint=endpoint, status_code=status_code)
                metrics.http_request_duration_seconds.observe(duration, method=method, endpoint=endpoint)

            response.headers["X-Correlation-ID"] = cid
            return response
        except Exception:
            duration = time.perf_counter() - start_time
            if endpoint != "/metrics":
                metrics.http_requests_total.inc(method=method, endpoint=endpoint, status_code="500")
                metrics.http_request_duration_seconds.observe(duration, method=method, endpoint=endpoint)
            raise
