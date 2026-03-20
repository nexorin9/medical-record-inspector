"""
Medical Record Inspector - Main Application Entry Point

FastAPI server for medical record quality evaluation using LLM.
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .api import evaluator
from .api import templates


# Configure CORS origins from environment or default to localhost
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    print("Medical Record Inspector starting up...")
    yield
    # Shutdown
    print("Medical Record Inspector shutting down...")


app = FastAPI(
    title="Medical Record Inspector API",
    description="API for medical record quality evaluation using LLM",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Medical Record Inspector",
        "version": "1.0.0",
    }


# Include routers
app.include_router(evaluator.router, prefix="/api/v1", tags=["evaluator"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Record Inspector API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
