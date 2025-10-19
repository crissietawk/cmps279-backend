"""
Medical Management System - FastAPI Backend
Complete API with authentication, dashboard, patients, doctors, surgeries, OR schedule, 
recording, notes, analysis, and notifications
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routes import api_router
from app.db import get_connection
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Medical Management System API",
    description="Complete backend API for hospital management system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes with /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Test database connection on startup"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Medical Management System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "dashboard": "/api/v1/dashboard",
            "patients": "/api/v1/patients",
            "doctors": "/api/v1/doctors",
            "surgeries": "/api/v1/surgeries",
            "or_schedule": "/api/v1/calendar",
            "recording": "/api/v1/transcriptions",
            "notes": "/api/v1/notes",
            "analysis": "/api/v1/analysis",
            "notifications": "/api/v1/notifications"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
