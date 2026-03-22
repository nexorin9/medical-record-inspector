"""
Template API routes for medical record templates management.
"""

import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from templates.store import TemplateStore
from models.template import Template

router = APIRouter()

# Global template store instance
_template_store: Optional[TemplateStore] = None


def get_template_store() -> TemplateStore:
    """Get or create template store instance."""
    global _template_store
    if _template_store is None:
        _template_store = TemplateStore()
    return _template_store


# Request/Response models
class TemplateCreateRequest(BaseModel):
    """Request model for creating a template."""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: str = Field(..., min_length=1, max_length=500, description="模板描述")
    content: str = Field(..., min_length=1, description="模板内容（高质量病历文本）")
    tags: Optional[List[str]] = Field(default_factory=list, description="模板标签")


class TemplateUpdateRequest(BaseModel):
    """Request model for updating a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="模板描述")
    content: Optional[str] = Field(None, min_length=1, description="模板内容")
    tags: Optional[List[str]] = Field(default=None, description="模板标签")


class TemplateResponse(BaseModel):
    """Response model for template."""
    id: str
    name: str
    description: str
    content: str
    created_at: datetime
    updated_at: datetime
    version: int
    tags: List[str]


class TemplateListResponse(BaseModel):
    """Response model for template list."""
    total: int
    templates: List[TemplateResponse]


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    limit: int = 100,
    offset: int = 0
):
    """
    List all templates.

    Args:
        limit: Maximum number of templates to return
        offset: Number of templates to skip

    Returns:
        TemplateListResponse with total count and templates list
    """
    try:
        store = get_template_store()
        templates = store.list_templates(limit=limit, offset=offset)

        return TemplateListResponse(
            total=len(templates),
            templates=[
                TemplateResponse(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    content=t.content,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    version=t.version,
                    tags=t.tags or []
                )
                for t in templates
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """
    Get a specific template by ID.

    Args:
        template_id: Template ID

    Returns:
        TemplateResponse with template details

    Raises:
        HTTPException: If template not found
    """
    try:
        store = get_template_store()
        template = store.get_template(template_id)

        if template is None:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        return TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            content=template.content,
            created_at=template.created_at,
            updated_at=template.updated_at,
            version=template.version,
            tags=template.tags or []
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(request: TemplateCreateRequest = Body(...)):
    """
    Create a new template.

    Args:
        request: TemplateCreateRequest with template data

    Returns:
        TemplateResponse with created template details
    """
    try:
        store = get_template_store()

        template = Template(
            name=request.name,
            description=request.description,
            content=request.content,
            tags=request.tags
        )

        saved_template = store.save_template(template)

        return TemplateResponse(
            id=saved_template.id,
            name=saved_template.name,
            description=saved_template.description,
            content=saved_template.content,
            created_at=saved_template.created_at,
            updated_at=saved_template.updated_at,
            version=saved_template.version,
            tags=saved_template.tags or []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    request: TemplateUpdateRequest = Body(...)
):
    """
    Update an existing template.

    Args:
        template_id: Template ID to update
        request: TemplateUpdateRequest with new data

    Returns:
        TemplateResponse with updated template details

    Raises:
        HTTPException: If template not found
    """
    try:
        store = get_template_store()
        template = store.get_template(template_id)

        if template is None:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        # Update fields if provided
        if request.name is not None:
            template.name = request.name
        if request.description is not None:
            template.description = request.description
        if request.content is not None:
            template.content = request.content
        if request.tags is not None:
            template.tags = request.tags

        saved_template = store.save_template(template)

        return TemplateResponse(
            id=saved_template.id,
            name=saved_template.name,
            description=saved_template.description,
            content=saved_template.content,
            created_at=saved_template.created_at,
            updated_at=saved_template.updated_at,
            version=saved_template.version,
            tags=saved_template.tags or []
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(template_id: str):
    """
    Delete a template.

    Args:
        template_id: Template ID to delete

    Returns:
        Empty response with 204 status

    Raises:
        HTTPException: If template not found
    """
    try:
        store = get_template_store()
        template = store.get_template(template_id)

        if template is None:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        deleted = store.delete_template(template_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete template")

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


@router.get("/templates/{template_id}/history")
async def get_template_history(template_id: str):
    """
    Get version history for a template.

    Args:
        template_id: Template ID

    Returns:
        List of template versions with timestamps

    Raises:
        HTTPException: If template not found
    """
    try:
        store = get_template_store()
        template = store.get_template(template_id)

        if template is None:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        # Load all data to get version history
        data = store._load()

        if template_id not in data:
            return {"versions": []}

        # Since we only store current version, return current template info
        # In a full implementation, you'd store version history separately
        return {
            "template_id": template_id,
            "current_version": template.version,
            "versions": [
                {
                    "version": template.version,
                    "updated_at": template.updated_at.isoformat(),
                    "name": template.name
                }
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template history: {str(e)}")
