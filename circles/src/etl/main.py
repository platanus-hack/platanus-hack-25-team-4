"""
FastAPI Application - Main entry point for the ETL API.

Exposes endpoints for uploading and processing data across 10 data types.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routers import consolidation, upload
from .core import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response


# Create FastAPI app
app = FastAPI(
    title="Circles ETL",
    description="Data ingestion and transformation for Active Circles platform",
    version="0.1.0",
)

# Configure CORS - restrict to allowed origins from environment
settings = get_settings()
allowed_origins = [
    "http://localhost:3000",  # TS backend (default port)
    "http://localhost:5173",  # Local development - Vite frontend
    "http://localhost:8080",  # Local development - alternative
]

# Add production origins if configured
if hasattr(settings, "frontend_url") and settings.frontend_url:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(upload.router)
app.include_router(consolidation.router)


@app.get("/")
async def root():
    """Health check endpoint - matches TS backend response."""
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """Detailed health check - matches TS backend format."""
    return {"status": "ok"}


@app.get("/api/v1/info")
async def info():
    """API information."""
    return {
        "endpoints": {
            "resume": "POST /api/v1/upload/resume",
            "photo": "POST /api/v1/upload/photo",
            "voice_note": "POST /api/v1/upload/voice-note",
            "chat_transcript": "POST /api/v1/upload/chat-transcript",
            "calendar": "POST /api/v1/upload/calendar",
            "status": "GET /api/v1/upload/status/{job_id}",
        },
        "supported_data_types": [
            "resume",
            "photo",
            "voice_note",
            "chat_transcript",
            "email",
            "calendar",
            "social_post",
            "blog_post",
            "screenshot",
            "shared_image",
        ],
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Convert HTTPException detail field to error field for API consistency."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.log_level.lower())
