"""
Main FastAPI application
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import api_router
from app.api.ultra_endpoints import ultra_router
from app.models.database import create_tables

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gid_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Global ID Management System...")
    
    # Create database tables
    try:
        # Skip automatic table creation since tables are manually created via pgAdmin
        logger.info("Database tables already exist, skipping automatic creation...")
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
    
    yield
    
    logger.info("Shutting down Global ID Management System...")


# Create FastAPI application
app = FastAPI(
    title="Global ID Management System",
    description="Centralized Global ID (G_ID) management system with real-time synchronization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(api_router)

# Include ultra-performance routes for million-record processing
app.include_router(ultra_router, prefix="/api/v1/ultra", tags=["Ultra Performance"])


# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/database-explorer", response_class=HTMLResponse)
async def database_explorer(request: Request):
    """Database explorer page - shows all tables and data from both databases"""
    return templates.TemplateResponse("database_explorer.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def excel_upload(request: Request):
    """Excel upload page"""
    return templates.TemplateResponse("excel_upload.html", {"request": request})


@app.get("/sync", response_class=HTMLResponse)
async def sync_management(request: Request):
    """Sync management page"""
    return templates.TemplateResponse("sync_management.html", {"request": request})


@app.get("/monitoring", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    """Monitoring page"""
    return templates.TemplateResponse("monitoring.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )