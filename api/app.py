"""
FastAPI application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from .routes import router
from .frontend import frontend_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Sports Calendar API",
        description="API for collecting and viewing sports schedules",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(router, prefix="/api/v1", tags=["api"])
    
    # Include frontend routes
    app.include_router(frontend_router, tags=["frontend"])
    
    # Static files for frontend
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    return app
