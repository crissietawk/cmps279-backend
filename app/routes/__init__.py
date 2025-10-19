
"""
Routes package - Combines all API routers
"""
from fastapi import APIRouter

# Import all route modules
from app.routes import (
    auth,
    dashboard,
    patients,
    doctors,
    or_schedule,
    surgeries,
    recording,
    notes,
    analysis,
    notifications
)

# Create main API router
api_router = APIRouter()

# Include all sub-routers with their prefixes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(or_schedule.router, tags=["OR Schedule"])
api_router.include_router(surgeries.router, prefix="/surgeries", tags=["Surgeries"])
api_router.include_router(recording.router, prefix="/transcriptions", tags=["Recording"])
api_router.include_router(notes.router, prefix="/notes", tags=["Notes"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
