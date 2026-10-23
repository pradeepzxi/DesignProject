"""FastAPI Application Main Entrypoint.

Intelligent Link Integrity Management and Autonomous Remediation Framework
for Enterprise Document Repositories (Research Prototype).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.core.logging_config import setup_logging, logger
from backend.app.api.router import api_router
# Import all models to ensure metadata registration
import backend.app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured logging
    setup_logging()
    logger.info("Initializing Link Integrity Platform Database Tables...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"{settings.APP_NAME} started successfully on {settings.ENVIRONMENT} mode.")
    yield
    logger.info("Shutting down Link Integrity Platform...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Research prototype for autonomous hyperlink integrity management, "
        "failure classification, and contextual remediation in enterprise repositories."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "error": str(exc)},
    )


# Mount Static Files for documents repository
app.mount("/static/documents", StaticFiles(directory=str(settings.DOCUMENTS_DIR)), name="documents")

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "sqlite_connected",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
