"""
LM Studio Manager Routes Registration
Add this section to backend/app/main_updated.py after the dashboard router registration.
"""

# ============================================
# LM STUDIO MANAGER ROUTES
# ============================================

from app.api.lmstudio.routes import router as lmstudio_router
app.include_router(lmstudio_router)
