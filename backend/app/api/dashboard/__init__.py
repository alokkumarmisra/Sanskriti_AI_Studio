"""Agent Monitoring Dashboard APIs."""

from fastapi import APIRouter

from .agents import router as agents_router
from .executions import router as executions_router
from .logs import router as logs_router
from .current_activity import router as activity_router

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Include all sub-routers
dashboard_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
dashboard_router.include_router(executions_router, prefix="/executions", tags=["Executions"])
dashboard_router.include_router(logs_router, prefix="/logs", tags=["Logs"])
dashboard_router.include_router(activity_router, prefix="/activity", tags=["Activity"])
