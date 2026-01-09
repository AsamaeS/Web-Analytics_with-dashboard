"""
Projects API router.
Handles CRUD operations for projects.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
from ..storage import db_manager
from ..storage.models import Project

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(project: Project) -> dict:
    """Create a new project."""
    try:
        project_id = db_manager.create_project(project)
        return {"id": project_id, "message": "Project created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/", response_model=List[Project])
async def list_projects() -> List[Project]:
    """List all projects."""
    return db_manager.list_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """Get project by ID."""
    project = db_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return project


@router.put("/{project_id}")
async def update_project(project_id: str, updates: dict) -> dict:
    """Update project fields."""
    success = db_manager.update_project(project_id, updates)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return {"message": "Project updated successfully"}


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> dict:
    """Delete project and all associated sources."""
    success = db_manager.delete_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    return {"message": "Project deleted successfully"}
