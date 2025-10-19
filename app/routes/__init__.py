"""
Routes package - Combines all API routers
"""
from fastapi import APIRouter

# Import route modules using relative imports (NOT from app.routes)
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .patients import router as patients_router
from .doctors import router as doctors_router
from .or_schedule import router as or_schedule_router
from .surgeries import router as surgeries_router
from .recording import router as recording_router
from .notes import router as notes_router
from .analysis import router as analysis_router
from .notifications import router as notifications_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers with their prefixes
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(patients_router, prefix="/patients", tags=["Patients"])
api_router.include_router(doctors_router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(or_schedule_router, tags=["OR Schedule"])
api_router.include_router(surgeries_router, prefix="/surgeries", tags=["Surgeries"])
api_router.include_router(recording_router, prefix="/transcriptions", tags=["Recording"])
api_router.include_router(notes_router, prefix="/notes", tags=["Notes"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
