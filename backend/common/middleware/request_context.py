"""Request context middleware for audit logging (IP address & request ID)."""
from contextvars import ContextVar
import uuid

_request_context: ContextVar[dict] = ContextVar("request_context", default={})


def get_request_context() -> dict:
    return _request_context.get()


def _extract_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        token = _request_context.set(
            {
                "request_id": request_id,
                "ip_address": _extract_client_ip(request),
                "path": request.path,
                "method": request.method,
            }
        )
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            _request_context.reset(token)
