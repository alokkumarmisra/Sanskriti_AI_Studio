# Sanskriti AI Studio API - Main Entry Point
# Uses direct database connection to avoid import chain issues

from fastapi import FastAPI, HTTPException
import json
import uuid

app = FastAPI(title="Sanskriti AI Studio API")


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
    return {"status": "ok"}


@app.get("/app/info")
async def app_info():
    """Application info endpoint."""
    try:
        from app.core.config import config
        return {
            "name": "Sanskriti AI Studio",
            "version": getattr(config, "API_VERSION", "1.0.0"),
            "status": "running",
        }
    except ImportError:
        return {"name": "Sanskriti AI Studio", "version": "1.0.0", "status": "running"}


# Include projects routes
from app.api.projects.routes import router as projects_router
app.include_router(projects_router)

# Include scenes/characters/locations routes (Content & Scene Planning)
from app.api.projects.scenes import router as scenes_router
app.include_router(scenes_router, prefix="/api/v1")

# Include LM Studio routes
from app.api.lmstudio.routes import router as lmstudio_router
app.include_router(lmstudio_router)

# Include dashboard routes
from app.api.dashboard.routes import router as dashboard_router
app.include_router(dashboard_router)


@app.get("/api/v1/projects")
async def list_projects():
    """Retrieve all projects."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, description, project_type, status, created_at, updated_at FROM projects ORDER BY name")
        )
        rows = result.fetchall()

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "project_type": row.project_type,
                    "status": row.status,
                    "created_at": str(row.created_at),
                    "updated_at": str(row.updated_at),
                }
                for row in rows
            ],
            "message": "Projects retrieved successfully",
        }


@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str):
    """Retrieve a single project by ID."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, description, project_type, status, created_at, updated_at FROM projects WHERE id = :project_id"),
            {"project_id": project_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "project_type": row.project_type,
                    "status": row.status,
                    "created_at": str(row.created_at),
                    "updated_at": str(row.updated_at),
                }
            ],
            "message": "Project retrieved successfully",
        }


@app.post("/api/v1/projects")
async def create_project(payload: dict):
    """Create a new project."""
    from app.core.database import engine
    from sqlalchemy import text
    import re

    if not payload.get("name"):
        raise HTTPException(status_code=400, detail="Project name is required")

    with engine.connect() as conn:
        name = payload.get("name", "")
        description = payload.get("description") or None
        project_type = payload.get("project_type", "general")
        slug = payload.get("slug") if payload.get("slug") else re.sub(r'[^\w\s-]', '', name.lower()).strip().replace(' ', '-')

        conn.execute(
            text("""
                INSERT INTO projects (id, name, description, project_type, status, slug, created_at, updated_at)
                VALUES (:id, :name, :description, :project_type, :status, :slug, NOW(), NOW())
            """),
            {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": description,
                "project_type": project_type,
                "status": payload.get("status") or "draft",
                "slug": slug,
            }
        )
        conn.commit()

        result = conn.execute(
            text("SELECT id, name, description, project_type, status, created_at, updated_at FROM projects WHERE slug = :slug ORDER BY id DESC LIMIT 1"),
            {"slug": slug}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create project")

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "project_type": row.project_type,
                    "status": row.status,
                    "created_at": str(row.created_at),
                    "updated_at": str(row.updated_at),
                }
            ],
            "message": "Project created successfully",
        }


@app.put("/api/v1/projects/{project_id}")
async def update_project(project_id: str, payload: dict):
    """Update an existing project."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        name = payload.get("name")
        description = payload.get("description")
        project_type = payload.get("project_type")
        status = payload.get("status")

        update_fields = []
        values = {}

        if name is not None:
            update_fields.append("name = :name")
            values["name"] = name
        if description is not None:
            update_fields.append("description = :description")
            values["description"] = description
        if project_type is not None:
            update_fields.append("project_type = :project_type")
            values["project_type"] = project_type
        if status is not None:
            update_fields.append("status = :status")
            values["status"] = status
        update_fields.append("updated_at = NOW()")

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = conn.execute(
            text("SELECT id FROM projects WHERE id = :id"),
            {"id": project_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        values["id"] = project_id
        set_clause = ", ".join(update_fields)
        conn.execute(
            text(f"UPDATE projects SET {set_clause} WHERE id = :id"),
            values
        )
        conn.commit()

        result = conn.execute(
            text("SELECT id, name, description, project_type, status, created_at, updated_at FROM projects WHERE id = :id"),
            {"id": project_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found after update")

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "project_type": row.project_type,
                    "status": row.status,
                    "created_at": str(row.created_at),
                    "updated_at": str(row.updated_at),
                }
            ],
            "message": "Project updated successfully",
        }


@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM projects WHERE id = :id"),
            {"id": project_id}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        conn.execute(text("DELETE FROM projects WHERE id = :id"), {"id": project_id})
        conn.commit()

        return {
            "success": True,
            "data": [],
            "message": "Project deleted successfully",
        }


# ============================================
# LYRICS ENDPOINTS
# ============================================

@app.get("/api/v1/lyrics/search")
async def search_lyrics(query: str, project_id: str | None = None):
    """Search lyrics across all projects or within a specific project."""
    from app.core.database import engine
    from sqlalchemy import text
    
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    if project_id:
        search_query = """
            SELECT l.id, p.name as project_name, l.title, l.content, l.language, l.status, l.created_at, l.updated_at
            FROM lyrics l
            JOIN projects p ON l.project_id = p.id
            WHERE LOWER(l.content) LIKE :query AND l.project_id = :project_id
        """
    else:
        search_query = """
            SELECT l.id, p.name as project_name, l.title, l.content, l.language, l.status, l.created_at, l.updated_at
            FROM lyrics l
            JOIN projects p ON l.project_id = p.id
            WHERE LOWER(l.content) LIKE :query
        """

    with engine.connect() as conn:
        result = conn.execute(text(search_query), {"query": f"%{query}%", "project_id": project_id if project_id else None})
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


@app.get("/api/v1/projects/{project_id}/lyrics")
async def list_project_lyrics(project_id: str):
    """List all lyrics for a specific project."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, title, content, language, status FROM lyrics WHERE project_id = :project_id ORDER BY title"),
            {"project_id": project_id}
        )
        rows = result.fetchall()

        return {
            "success": True,
            "data": [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "content": row.content,
                    "language": row.language,
                    "status": row.status,
                }
                for row in rows
            ],
            "message": f"Found {len(rows)} lyrics for this project",
        }


@app.post("/api/v1/projects/{project_id}/lyrics")
async def create_lyrics(project_id: str, payload: dict):
    """Create a new lyrics entry for a project."""
    from app.core.database import engine
    from sqlalchemy import text

    if not payload.get("title"):
        raise HTTPException(status_code=400, detail="Lyrics title is required")

    with engine.connect() as conn:
        id_val = str(uuid.uuid4())
        
        conn.execute(
            text("""
                INSERT INTO lyrics (id, project_id, title, content, language, status, created_at, updated_at)
                VALUES (:id, :project_id, :title, :content, :language, :status, NOW(), NOW())
            """),
            {
                "id": id_val,
                "project_id": project_id,
                "title": payload.get("title"),
                "content": payload.get("content") or "",
                "language": payload.get("language") or "English",
                "status": payload.get("status") or "draft",
            }
        )
        conn.commit()

        result = conn.execute(
            text("SELECT id, project_id, title, content, language, status FROM lyrics WHERE id = :id"),
            {"id": id_val}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create lyrics")

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
            "message": "Lyrics created successfully",
        }


@app.put("/api/v1/lyrics/{lyrics_id}")
async def update_lyrics(lyrics_id: str, payload: dict):
    """Update an existing lyrics entry."""
    from app.core.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
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


