# Phase 3: FastAPI Application Entry Point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import routers
from api.routers import brands, search, auth, websocket, testing, mentions

# Create FastAPI app
app = FastAPI(
    title="BrandPulse API",
    description="Real-time brand sentiment analysis and monitoring API",
    version="3.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc UI
)

# CORS middleware - allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {
        "status": "healthy",
        "service": "BrandPulse API",
        "version": "3.0.0"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Welcome to BrandPulse API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

# Include routers
app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(search.router)
app.include_router(websocket.router)
app.include_router(testing.router)  # Development only
app.include_router(mentions.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize connections on startup
    """
    print("🚀 BrandPulse API starting up...")
    print("📚 API Documentation: http://localhost:8000/docs")

    # Initialize WebSocket service with connection manager
    from services.websocket_service import websocket_service
    from api.routers.websocket import manager
    websocket_service.set_manager(manager)
    print("🔌 WebSocket service initialized")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up connections on shutdown
    """
    print("👋 BrandPulse API shutting down...")


if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    # Run the server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )
