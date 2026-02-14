"""FastAPI application — serves the ProSim REST API."""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from prosim.api.routes import router

app = FastAPI(
    title="ProSim API",
    description="Workflow simulation engine REST API",
    version="0.2.0",
)

# CORS — configurable via PROSIM_CORS_ORIGINS env var (comma-separated).
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_origins = os.environ.get("PROSIM_CORS_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(router, prefix="/api")


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):  # noqa: ARG001
    """Return 422 with structured error for Pydantic validation failures."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):  # noqa: ARG001
    """Return 422 for value errors (invalid enum values, etc.)."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the uvicorn server."""
    uvicorn.run(app, host=host, port=port)
