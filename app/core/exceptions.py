from fastapi import Request, status
from fastapi.responses import JSONResponse
from google.api_core import exceptions as google_exceptions

async def google_exception_handler(request: Request, exc: google_exceptions.GoogleAPICallError):
    """
    Trata erros vindos das bibliotecas do Google Cloud.
    Retorna 502 Bad Gateway para indicar erro upstream.
    """
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": "Upstream Error from Google Cloud Platform",
            "google_error": str(exc.message) if hasattr(exc, "message") else str(exc),
            "code": exc.code if hasattr(exc, "code") else 502
        },
    )

async def global_exception_handler(request: Request, exc: Exception):
    """
    Trata erros genéricos não previstos.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "error": str(exc)
        },
    )
