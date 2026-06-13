"""
LLM Observability Dashboard – FastAPI application entry point.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.config import settings
from backend.database import create_tables
from backend.telemetry import setup_telemetry
from backend.utils.logging_config import setup_logging, get_logger
from backend.utils.helpers import generate_request_id
from backend.routes import logs as logs_router
from backend.routes import metrics as metrics_router
from backend.routes import evals as evals_router
from backend.routes import upload as upload_router
from backend.routes import auth as auth_router

# ---------------------------------------------------------------------------
# Logging – initialised before anything else
# ---------------------------------------------------------------------------
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – creating tables if needed…")
    create_tables()
    logger.info("App started on http://%s:%s", settings.API_HOST, settings.API_PORT)
    yield
    logger.info("Shutting down – closing database connections.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="LLM Observability Dashboard API",
    description="API for monitoring and analysing LLM applications",
    version="1.0.0",
    lifespan=lifespan,
)

# OTEL must be wired before the app starts (before any middleware is locked in)
setup_telemetry(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Logging middleware – attaches request_id + logs every request/response
# ---------------------------------------------------------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = generate_request_id()
    request.state.request_id = request_id
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request_id=%s method=%s path=%s status=%d latency_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"
    return response


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "LLM Observability Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# Feature routers
# ---------------------------------------------------------------------------
app.include_router(logs_router.router)
app.include_router(metrics_router.router)
app.include_router(evals_router.router)
app.include_router(upload_router.router)
app.include_router(auth_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
    )
