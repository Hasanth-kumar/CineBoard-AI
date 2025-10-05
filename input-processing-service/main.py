"""
Input Processing Service - Main Application
Handles Phase 1 of the video generation pipeline: input processing and validation
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import structlog
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import init_db
from app.core.redis import init_redis
from app.api.v1.router import api_router
from app.core.middleware import LoggingMiddleware, MetricsMiddleware
from app.core.exceptions import InputProcessingException

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics (only unique ones not defined in middleware)
INPUT_PROCESSING_COUNT = Counter('input_processing_total', 'Total input processing requests', ['status', 'language'])

# Create FastAPI application
app = FastAPI(
    title="Input Processing Service",
    description="Phase 1: Input processing and validation for video generation platform",
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Global exception handler
@app.exception_handler(InputProcessingException)
async def input_processing_exception_handler(request: Request, exc: InputProcessingException):
    logger.error("Input processing error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "error_code": exc.error_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unexpected error", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "error_code": "INTERNAL_ERROR"}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Input Processing Service", version=settings.SERVICE_VERSION)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")
    
    logger.info("Input Processing Service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Input Processing Service")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy",
        "service": "input-processing-service",
        "version": settings.SERVICE_VERSION,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    # Add database and Redis connectivity checks here
    return {"status": "ready"}

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Input Processing Service",
        "version": settings.SERVICE_VERSION,
        "description": "Phase 1: Input processing and validation for video generation platform",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

