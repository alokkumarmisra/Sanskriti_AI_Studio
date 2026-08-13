"""API package."""

from .auth import router as auth_router
from .projects import router as projects_router  
from .tasks import router as tasks_router
from .dashboard import dashboard_router

# Import to register all routers
import app.main

# Dashboard router - Agent Monitoring Dashboard
# Include at the main router level if needed
