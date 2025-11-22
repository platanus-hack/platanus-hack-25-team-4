"""
FastAPI Application - Main entry point for the ETL API.

Exposes endpoints for uploading and processing data across 10 data types.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routers import upload
from .core import get_settings

# Create FastAPI app
app = FastAPI(
    title="Circles ETL",
    description="Data ingestion and transformation for Active Circles platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Circles ETL API", "version": "0.1.0", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Detailed health check."""
    settings = get_settings()

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "debug": settings.debug,
    }


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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.log_level.lower())
