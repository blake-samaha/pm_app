"""FastAPI application entry point."""
import sys
import traceback
import logging
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import text
from database import create_db_and_tables, engine
from config import get_settings
import models  # Import to register all models with SQLModel
from routers import auth, projects, actions, risks, sync
from exceptions import (
    PMAppException,
    ResourceNotFoundError,
    AuthorizationError,
    AuthenticationError,
    ValidationError,
    DuplicateResourceError,
    IntegrationError,
    ConfigurationError,
)
from integrations import JiraClient, PrecursiveClient

settings = get_settings()


# ============================================================================
# Structured Logging Configuration
# ============================================================================

def configure_logging():
    """Configure structured logging with structlog."""
    
    # Determine log level based on environment
    log_level = logging.DEBUG if settings.environment == "development" else logging.INFO
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            # Use console renderer in dev, JSON in production
            structlog.dev.ConsoleRenderer() if settings.environment == "development" 
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Initialize logging
configure_logging()
logger = structlog.get_logger()


# ============================================================================
# Startup Validation
# ============================================================================

def validate_required_config():
    """
    Validate required configuration on startup.
    Fail fast if critical settings are missing.
    """
    errors = []
    
    # Database (required)
    if not settings.database_url:
        errors.append("DATABASE_URL is required")
    
    # JWT (required)
    if not settings.secret_key:
        errors.append("SECRET_KEY is required")
    
    # Firebase (required for auth)
    if not settings.firebase_project_id:
        errors.append("FIREBASE_PROJECT_ID is required")
    
    if errors:
        for error in errors:
            logger.error("Configuration error", error=error)
        raise ConfigurationError(
            f"Missing required configuration: {', '.join(errors)}"
        )
    
    logger.info("Configuration validated successfully")


def log_integration_status():
    """Log the status of optional integrations."""
    jira_client = JiraClient(settings)
    precursive_client = PrecursiveClient(settings)
    
    if jira_client.is_configured:
        logger.info("Jira integration", status="configured", base_url=settings.jira_base_url)
    else:
        logger.warning("Jira integration", status="not configured", 
                      hint="Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN")
    
    if precursive_client.is_configured:
        logger.info("Precursive integration", status="configured", 
                   instance_url=settings.precursive_instance_url)
    else:
        logger.warning("Precursive integration", status="not configured",
                      hint="Set PRECURSIVE_INSTANCE_URL and credentials")


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting PM App API", version="1.0.0", environment=settings.environment)
    
    # Validate configuration (fail fast)
    validate_required_config()
    
    # Create database tables
    create_db_and_tables()
    logger.info("Database tables initialized")
    
    # Log integration status
    log_integration_status()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="PM App API",
    description="Automated Project Management Tool API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

def create_error_response(
    status_code: int, 
    detail: str, 
    error_type: str,
    include_trace: bool = False,
    exc: Exception = None
) -> dict[str, Any]:
    """Create a consistent error response."""
    response = {
        "detail": detail,
        "error_type": error_type,
        "status_code": status_code,
    }
    
    # Include stack trace in development mode
    if include_trace and exc and settings.environment == "development":
        response["traceback"] = traceback.format_exception(type(exc), exc, exc.__traceback__)
    
    return response


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    """Handle resource not found errors."""
    logger.warning("Resource not found", path=request.url.path, detail=str(exc))
    return JSONResponse(
        status_code=404,
        content=create_error_response(404, str(exc), "ResourceNotFoundError")
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    logger.warning("Authorization denied", path=request.url.path, detail=str(exc))
    return JSONResponse(
        status_code=403,
        content=create_error_response(403, str(exc), "AuthorizationError")
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning("Authentication failed", path=request.url.path, detail=str(exc))
    return JSONResponse(
        status_code=401,
        content=create_error_response(401, str(exc), "AuthenticationError"),
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle business validation errors."""
    logger.warning("Validation error", path=request.url.path, detail=str(exc))
    return JSONResponse(
        status_code=400,
        content=create_error_response(400, str(exc), "ValidationError")
    )


@app.exception_handler(DuplicateResourceError)
async def duplicate_resource_handler(request: Request, exc: DuplicateResourceError):
    """Handle duplicate resource errors."""
    logger.warning("Duplicate resource", path=request.url.path, detail=str(exc))
    return JSONResponse(
        status_code=409,
        content=create_error_response(409, str(exc), "DuplicateResourceError")
    )


@app.exception_handler(IntegrationError)
async def integration_error_handler(request: Request, exc: IntegrationError):
    """Handle integration/external service errors."""
    logger.error("Integration error", path=request.url.path, detail=str(exc), exc_info=exc)
    return JSONResponse(
        status_code=502,
        content=create_error_response(
            502, str(exc), "IntegrationError", 
            include_trace=True, exc=exc
        )
    )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle configuration errors."""
    logger.error("Configuration error", path=request.url.path, detail=str(exc))
    return JSONResponse(
        status_code=500,
        content=create_error_response(500, str(exc), "ConfigurationError")
    )


@app.exception_handler(PMAppException)
async def pm_app_exception_handler(request: Request, exc: PMAppException):
    """Handle general application errors."""
    logger.error("Application error", path=request.url.path, detail=str(exc), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            500, 
            str(exc) if settings.environment == "development" else "An internal error occurred",
            "PMAppException",
            include_trace=True,
            exc=exc
        )
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.error("Unhandled exception", path=request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            500,
            str(exc) if settings.environment == "development" else "An unexpected error occurred",
            type(exc).__name__,
            include_trace=True,
            exc=exc
        )
    )


# ============================================================================
# Routers
# ============================================================================

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(actions.router)
app.include_router(risks.router)
app.include_router(sync.router)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "PM App API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns status of all services and connections.
    """
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "services": {}
    }
    
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = {"status": "connected"}
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = {
            "status": "error",
            "error": str(e) if settings.environment == "development" else "Connection failed"
        }
    
    # Check Jira connection (if configured)
    jira_client = JiraClient(settings)
    if jira_client.is_configured:
        try:
            jira_status = await jira_client.test_connection()
            health_status["services"]["jira"] = jira_status
        except IntegrationError as e:
            health_status["status"] = "degraded"
            health_status["services"]["jira"] = {
                "status": "error",
                "error": str(e)
            }
        finally:
            await jira_client.close()
    else:
        health_status["services"]["jira"] = {"status": "not_configured"}
    
    # Check Precursive connection (if configured)
    precursive_client = PrecursiveClient(settings)
    if precursive_client.is_configured:
        try:
            precursive_status = await precursive_client.test_connection()
            health_status["services"]["precursive"] = precursive_status
        except IntegrationError as e:
            health_status["status"] = "degraded"
            health_status["services"]["precursive"] = {
                "status": "error",
                "error": str(e)
            }
        finally:
            await precursive_client.close()
    else:
        health_status["status"] = "degraded"
        health_status["services"]["precursive"] = {
            "status": "error",
            "error": "Precursive integration required but not configured",
        }
    
    # Set appropriate HTTP status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/health/live")
def liveness_check():
    """Simple liveness probe - just confirms the app is running."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness probe - confirms the app is ready to serve traffic.
    Checks database connectivity.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )
