from rest_framework import status
from rest_framework.response import Response


def success_response(
    data=None,
    message: str = "OK",
    status_code: int = status.HTTP_200_OK,
    meta: dict | None = None,
) -> Response:
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        payload["meta"] = meta
    return Response(payload, status=status_code)
