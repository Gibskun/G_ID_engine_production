"""
Main FastAPI application with environment detection
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from dotenv import load_dotenv

from app.api.routes import api_router
from app.api.ultra_endpoints import ultra_router
from app.models.database import create_tables

# Import environment configuration for automatic detection
try:
    from app.config.environment import env_config
    config = env_config.get_config()
except ImportError:
    # Fallback if environment config not available
    load_dotenv()
    config = {
        'app_host': os.getenv('APP_HOST', '127.0.0.1'),
        'app_port': int(os.getenv('APP_PORT', 8000)),
        'debug': os.getenv('DEBUG', 'True').lower() == 'true',
        'environment': 'unknown'
    }

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
    allow_origins=["*"],  # TODO: tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Honor X-Forwarded-* headers from nginx so FastAPI builds correct HTTPS absolute URLs
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(api_router)

# Include ultra-performance routes for million-record processing
app.include_router(ultra_router, prefix="/api/v1/ultra", tags=["Ultra Performance"])

# Create sub-application for /gid/ prefix to support local development
# This allows the system to work both locally (with /gid/ prefix) and on server (without prefix after Nginx rewrite)
gid_app = FastAPI(
    title="Global ID Management System - GID Prefix",
    description="Sub-application to handle /gid/ prefixed routes for local development compatibility",
    version="1.0.0",
    docs_url="/gid/docs",
    redoc_url="/gid/redoc"
)

# Add CORS middleware to sub-application
gid_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
gid_app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Mount static also on the sub-app so url_for('static', ...) resolves to /gid/static/...
gid_app.mount("/static", StaticFiles(directory="static"), name="static")

# Include same routes in sub-application
gid_app.include_router(api_router)
gid_app.include_router(ultra_router, prefix="/api/v1/ultra", tags=["Ultra Performance"])

# Add frontend routes to sub-application for /gid/ prefix compatibility
@gid_app.get("/", response_class=HTMLResponse)
async def gid_dashboard(request: Request):
    """Main dashboard page (GID prefix version)"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@gid_app.get("/database-explorer", response_class=HTMLResponse)
async def gid_database_explorer(request: Request):
    """Database explorer page (GID prefix version)"""
    return templates.TemplateResponse("database_explorer.html", {"request": request})

@gid_app.get("/upload", response_class=HTMLResponse)
async def gid_excel_upload(request: Request):
    """Excel upload page (GID prefix version)"""
    return templates.TemplateResponse("excel_upload.html", {"request": request})

@gid_app.get("/sync", response_class=HTMLResponse)
async def gid_sync_management(request: Request):
    """Sync management page (GID prefix version)"""
    return templates.TemplateResponse("sync_management.html", {"request": request})

@gid_app.get("/monitoring", response_class=HTMLResponse)
async def gid_monitoring_page(request: Request):
    """Monitoring page (GID prefix version)"""
    return templates.TemplateResponse("monitoring.html", {"request": request})

# Mount the sub-application at /gid/ path
app.mount("/gid", gid_app)


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
    
    # Use environment-aware configuration
    host = config['app_host']
    port = config['app_port']
    debug = config['debug']
    
    print(f"\n🚀 Starting Global ID Management System")
    print(f"   Environment: {config.get('environment', 'detected')}")
    print(f"   Server: http://{host}:{port}")
    print(f"   Debug Mode: {debug}")
    
    if config.get('environment') == 'local':
        print(f"   GID Routes: http://{host}:{port}/gid/")
        print(f"   API Docs: http://{host}:{port}/docs")
        print(f"   GID API Docs: http://{host}:{port}/gid/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )