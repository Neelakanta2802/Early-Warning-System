#!/usr/bin/env python3
"""
Entry point script for running the Early Warning System backend.
"""
import uvicorn
from config import settings
from pathlib import Path

if __name__ == "__main__":
    # CRITICAL: Ensure uvicorn imports `main.py` from THIS backend directory,
    # regardless of the current working directory (fixes "old code still running" issues).
    backend_dir = Path(__file__).resolve().parent
    uvicorn.run(
        "main:app",
        app_dir=str(backend_dir),
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        reload_dirs=[str(backend_dir)] if settings.api_reload else None,
        log_level=settings.log_level.lower()
    )
