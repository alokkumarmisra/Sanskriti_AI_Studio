"""CORS middleware for Sanskriti AI Studio backend."""

from typing import Callable, Awaitable
from fastapi import Request, Response


async def cors_middleware(app: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Add CORS headers to all responses.
    
    FastAPI middleware signature: (app: ASGIApp, scope: Scope) -> ASGIApp
    But we can use the Request-based approach by checking origin header.
    """
    
    # Get origins from request or use default
    origin = app.headers.get("origin", "")
    
    # Allow all origins for development, or restrict to configured origins
    if origin:
        allowed_origins = [origin]  # Dynamic allow based on incoming origin
    else:
        allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    async def handler(request: Request, call_next):
        response = await call_next(request)
        return Response(
            content=response.body(),
            status_code=response.status_code,
            headers={
                "Access-Control-Allow-Origin": ", ".join(allowed_origins),
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Vary": "Origin",
            },
        )
    
    # Return the handler function (ASGI middleware pattern)
    return handler