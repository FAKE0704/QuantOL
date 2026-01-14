"""FastAPI server for QuantOL.

This server provides RESTful API endpoints for the Next.js frontend
and handles authentication, business logic, and database interactions.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from .routers import auth, stocks, backtest, websocket


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan.

    Startup: Initialize database connections and services.
    Shutdown: Clean up resources.
    """
    # Startup
    print("FastAPI server starting up...")
    # Initialize database tables
    from src.database import get_db_adapter
    db = get_db_adapter()
    await db.initialize()
    print("Database initialized")
    yield
    # Shutdown
    print("FastAPI server shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="QuantOL API",
        description="RESTful API for QuantOL quantitative trading platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,https://quantol.com"
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(stocks.router, prefix="/api", tags=["stocks"])
    app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
    app.include_router(websocket.router, prefix="/api", tags=["websocket"])
    # app.include_router(charts.router, prefix="/api/charts", tags=["charts"])

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint for health check."""
        return {"message": "QuantOL API is running", "version": "0.1.0"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


# Create app instance for running directly
app = create_app()


def main() -> None:
    """Run the FastAPI server with uvicorn."""
    import uvicorn

    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8000"))

    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
