"""API package."""

from .auth import router as auth_router
# from .projects import router as projects_router  # Direct import in main.py
from .tasks import router as tasks_router
from .dashboard import dashboard_router
