from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import config
from app.core.logger import logger
from app.api import (
    pipeline_router,
    database_router,
    policy_router,
    reports_router,
    auth_router,
    websocket_router
)

# Initialize FastAPI application
app = FastAPI(
    title=config.API_TITLE,
    description="FastAPI Backend for Database Anonymization with WebSockets & Dynamic Reports",
    version=config.API_VERSION
)

# Enable CORS for developer access
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(pipeline_router)
app.include_router(database_router)
app.include_router(policy_router)
app.include_router(reports_router)
app.include_router(auth_router)
app.include_router(websocket_router)

# Mount static files for frontend
try:
    app.mount("/static", StaticFiles(directory="frontend-next/static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("DataVault AI Backend Server starting up")
    logger.info(f"API Title: {config.API_TITLE}")
    logger.info(f"API Version: {config.API_VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("DataVault AI Backend Server shutting down")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DataVault AI - Enterprise Backend Server",
        "version": config.API_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "datavault-backend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
