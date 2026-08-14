"""API routers package."""

from fastapi import APIRouter

# Projects router (includes lyrics and scenes endpoints)
from app.api.projects.routes import router as projects_router

# Combine routes
main_router = APIRouter()

# Register projects (which includes lyrics endpoints)
main_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
