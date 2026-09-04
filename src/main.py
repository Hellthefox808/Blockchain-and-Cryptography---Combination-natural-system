"""Main application entrypoint for the Blockchain and Cryptography Combo Nature System.

Initializes FastAPI, mounts API routers, configures CORS, and serves the interactive web UI.
"""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router as api_router

app = FastAPI(
    title="Blockchain & Cryptography Combo Nature System",
    description=(
        "An end-to-end engineered, cryptographically secure blockchain platform. "
        "Demonstrates SHA-256 avalanche effect, ECDSA asymmetric keypairs, "
        "Merkle tree root verification, Proof-of-Work consensus, and chain tamper detection."
    ),
    version="1.0.0",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API router
app.include_router(api_router)

# Mount static files directory if it exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "Blockchain & Cryptography Combo Nature System"}


@app.get("/", tags=["UI"])
def serve_dashboard() -> FileResponse:
    """Serve the single-page interactive web application dashboard."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return FileResponse(os.path.join(static_dir, "fallback.html")) if os.path.exists(
        os.path.join(static_dir, "fallback.html")
    ) else {"message": "Blockchain API active. Static dashboard index.html not found."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
