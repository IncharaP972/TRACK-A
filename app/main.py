"""
FastAPI application for the LatSpace Intelligent Excel Parser.

This module initializes the FastAPI application, configures middleware,
sets up logging, and includes the API routes.

Requirements: 1.2
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="LatSpace Intelligent Excel Parser",
    description="A FastAPI-based system that intelligently maps Excel file headers to a standardized data registry using a tiered matching strategy.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://frontend:3000",   # Docker container
        "http://127.0.0.1:3000",
        "*"  # Allow all origins for demo purposes
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["parser"])

logger.info("FastAPI application initialized")


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "LatSpace Intelligent Excel Parser",
        "version": "1.0.0",
        "description": "Upload Excel files to /api/parse for intelligent header mapping and data parsing",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
