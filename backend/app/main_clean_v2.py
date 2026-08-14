# Sanskriti AI Studio API - Main Entry Point (Clean with all lyrics CRUD)

from fastapi import FastAPI, HTTPException, Request
import json
import uuid
import re
from typing import Optional

app = FastAPI(title="Sanskriti AI Studio API", version="1.0.0")


# Add CORS middleware BEFORE including any routes
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "Sanskriti AI Studio"}


# Include projects routes (with lyrics endpoints)
from app.api.projects.routes import router as projects_router
app.include_router(projects_router, prefix="/api/v1")

# Include scenes/characters/locations routes (Content & Scene Planning)
from app.api.projects.scenes import router as scenes_router
app.include_router(scenes_router, prefix="/api/v1")

# Include LM Studio routes
from app.api.lmstudio.routes import router as lmstudio_router
app.include_router(lmstudio_router)

# Include dashboard routes
from app.api.dashboard.routes import router as dashboard_router
app.include_router(dashboard_router)


# ============================================
# STANDBALONE LYRICS CRUD ENDPOINTS (for global access)
# ============================================

@app.get("/api/v1/lyrics/search")
async def search_lyrics(query: str, project_id: str | None = None):
    """Search lyrics across all projects or within a specific project."""
    from app.core.database import engine
    from sqlalchemy import text
    
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    # Build search query based on whether we want to filter by project
    if project_id:
        search_query = f"""
            SELECT 
                l.id,
                p.name as project_name,
                l.title,
                l.content,
                l.language,
                l.status,
                l.created_at,
                l.updated_at
            FROM lyrics l
            JOIN projects p ON l.project_id = p.id
            WHERE LOWER(l.content) LIKE '%' || LOWER(:query) || '%'
              AND l.project_id = :project_id
        """
    else:
        search_query = f"""
            SELECT 
                l.id,
                p.name as project_name,
                l.title,
                l.content,
                l.language,
                l.status,
                l.created_at,
                l.updated_at
            FROM lyrics l
            JOIN projects p ON l.project_id = p.id
            WHERE LOWER(l.content) LIKE '%' || LOWER(:query) || '%'
        """

    with engine.connect() as conn:
        result = conn.execute(
            text(search_query),
            {"query": f"%{query}%", "project_id": project_id if project_id else None}
        )
        rows = result.fetchall()

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "project_name": row.project_name,
                    "title": row.title,
                    "content": row.content,
                    "language": row.language,
                    "status": row.status,
                    "created_at": str(row.created_at),
                    "updated_at": str(row.updated_at),
                }
                for row in rows
            ],
            "message": f"Found {len(rows)} lyrics matching search",
        }


@app.get("/api/v1/lyrics/{lyrics_id}")
async def get_lyrics(lyrics_id: str):
    """Get a specific lyrics entry by ID."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, project_id, title, content, language, status FROM lyrics WHERE id = :id"),
            {"id": lyrics_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Lyrics not found")

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "project_id": row.project_id,
                    "title": row.title,
                    "content": row.content,
                    "language": row.language,
                    "status": row.status,
                }
            ],
            "message": "Lyrics retrieved successfully",
        }


@app.put("/api/v1/lyrics/{lyrics_id}")
async def update_lyrics(lyrics_id: str, payload: dict):
    """Update an existing lyrics entry."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        # First check if lyrics exists
        result = conn.execute(text("SELECT id FROM lyrics WHERE id = :id"), {"id": lyrics_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Lyrics not found")

        update_fields = []
        values = {}

        if payload.get("title") is not None:
            update_fields.append("title = :name")
            values["name"] = payload.get("title")
        if payload.get("content") is not None:
            update_fields.append("content = :content")
            values["content"] = payload.get("content")
        if payload.get("language") is not None:
            update_fields.append("language = :language")
            values["language"] = payload.get("language")
        if payload.get("status") is not None:
            update_fields.append("status = :status")
            values["status"] = payload.get("status")
        update_fields.append("updated_at = NOW()")

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values["id"] = lyrics_id
        set_clause = ", ".join(update_fields)
        conn.execute(text(f"UPDATE lyrics SET {set_clause} WHERE id = :id"), values)
        conn.commit()

        result = conn.execute(
            text("SELECT id, project_id, title, content, language, status FROM lyrics WHERE id = :id"),
            {"id": lyrics_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Lyrics not found after update")

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "project_id": row.project_id,
                    "title": row.title,
                    "content": row.content,
                    "language": row.language,
                    "status": row.status,
                }
            ],
            "message": "Lyrics updated successfully",
        }


@app.delete("/api/v1/lyrics/{lyrics_id}")
async def delete_lyrics(lyrics_id: str):
    """Delete a lyrics entry."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM lyrics WHERE id = :id"), {"id": lyrics_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Lyrics not found")

        conn.execute(text("DELETE FROM lyrics WHERE id = :id"), {"id": lyrics_id})
        conn.commit()

        return {
            "success": True,
            "data": [],
            "message": "Lyrics deleted successfully",
        }
