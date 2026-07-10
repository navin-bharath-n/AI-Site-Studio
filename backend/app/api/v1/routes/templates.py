"""
Templates routes — public browsing and admin CRUD.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_user_optional, require_admin, require_seller_or_admin, get_current_user
from app.models.user import User
from app.services.template_service import TemplateService
from app.services.project_analyzer import project_analyzer
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateListResponse, TemplateFilterParams, TemplateCardResponse,
)
from app.models.template import TemplateFramework, TemplateLicense
from decimal import Decimal

router = APIRouter()


import httpx

class GitAnalyzeRequest(BaseModel):
    git_url: str
    token: Optional[str] = None


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    # Search
    q: Optional[str] = Query(None, description="Text search query"),
    # Category
    category: Optional[str] = Query(None, description="Category slug or name"),
    # Price
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    # Rating
    rating: Optional[float] = Query(None, ge=1, le=5),
    # Boolean flags
    is_free: Optional[bool] = Query(None),
    is_on_sale: Optional[bool] = Query(None),
    has_dark_mode: Optional[bool] = Query(None),
    is_ai_ready: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    # Taxonomy
    framework: Optional[TemplateFramework] = Query(None),
    industry: Optional[str] = Query(None),
    color_scheme: Optional[str] = Query(None),
    license_type: Optional[TemplateLicense] = Query(None),
    # Theme Forest specific filters
    sales: Optional[str] = Query(None, description="Sales count tier filter"),
    compatibility: Optional[str] = Query(None, description="Compatibility filter"),
    language: Optional[str] = Query(None, description="Programming language filter"),
    date_added: Optional[str] = Query(None, description="Date added range filter"),
    # Sorting & Pagination
    sort: str = Query("newest", description="Sort field"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    semantic: bool = Query(False, description="Use AI semantic search"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Browse marketplace templates with filtering, sorting, and pagination.
    All filter params are optional and combinable.
    """
    filters = TemplateFilterParams(
        q=q, category=category, min_price=min_price, max_price=max_price,
        rating=rating, is_free=is_free, is_on_sale=is_on_sale,
        has_dark_mode=has_dark_mode, is_ai_ready=is_ai_ready, is_featured=is_featured,
        framework=framework, industry=industry, color_scheme=color_scheme,
        license_type=license_type, sales=sales, compatibility=compatibility, language=language,
        date_added=date_added,
        sort=sort, page=page, page_size=page_size, semantic=semantic,
    )

    service = TemplateService(db)
    return await service.list_templates(filters, current_user)


@router.get("/featured", response_model=list[TemplateCardResponse])
async def get_featured_templates(
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Return featured templates for the landing page."""
    service = TemplateService(db)
    return await service.get_featured_templates(limit)


@router.get("/my-templates", response_model=list[TemplateResponse])
async def list_my_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    """
    Get all templates permanently linked to the current seller's account.
    Queries by seller_id FK — accurate regardless of name changes.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.template import Template
    from app.models.category import Category

    query = (
        select(Template)
        .options(selectinload(Template.category).selectinload(Category.children))
        .where(Template.seller_id == current_user.id)
        .order_by(Template.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{slug}", response_model=TemplateResponse)
async def get_template(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get full template details by slug."""
    service = TemplateService(db)
    return await service.get_template(slug, current_user)


@router.post("/analyze-zip")
async def analyze_project_zip(
    file: UploadFile = File(...),
    _user: User = Depends(require_seller_or_admin),
):
    """
    Upload a project ZIP file, extract it, analyze the code and assets,
    and generate visual/SEO/code suggestions and meta parameters via Gemini.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP archives are supported"
        )
    content = await file.read()
    return await project_analyzer.analyze_zip(content, file.filename)


@router.post("/analyze-git")
async def analyze_git_repo(
    request_data: GitAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    """
    Provide a Git repository URL, clone it, package it into a clean ZIP,
    analyze the code and assets, save the clean ZIP to database storage,
    and return the analysis results along with the public file URL.
    """
    git_url = request_data.git_url.strip()
    token = request_data.token.strip() if request_data.token else None
    if not token and current_user.github_access_token:
        token = current_user.github_access_token

    if not git_url.startswith(("http://", "https://", "git@")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Git URL format. Must start with http://, https:// or git@"
        )

    # Inject personal access token into HTTPS URL for private repositories
    if token and git_url.startswith("https://github.com/"):
        git_url = git_url.replace("https://github.com/", f"https://{token}@github.com/")

    try:
        result = await project_analyzer.analyze_git_repo(git_url)
        zip_bytes = result.pop("_zip_bytes")
        filename = result.pop("_filename")

        from app.core.storage import storage
        stored_zip_url = await storage.upload_file(
            db=db,
            file_content=zip_bytes,
            folder="uploads",
            original_filename=filename,
            content_type="application/zip",
        )

        result["stored_zip_url"] = stored_zip_url
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to import and analyze Git repository: {str(e)}"
        )


@router.get("/git-repos")
async def list_git_repos(
    username: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    current_user: User = Depends(require_seller_or_admin),
):
    """
    Fetch repository list for a GitHub user (using username or token, or stored user token).
    """
    auth_token = token
    if not auth_token and current_user.github_access_token:
        auth_token = current_user.github_access_token

    if not username and not auth_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either GitHub username, Personal Access Token, or connected GitHub account is required"
        )
    
    headers = {"Accept": "application/vnd.github+json"}
    if auth_token:
        headers["Authorization"] = f"token {auth_token}"
        url = "https://api.github.com/user/repos?per_page=100&sort=updated"
    else:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                detail = "Failed to fetch repositories from GitHub"
                try:
                    detail = response.json().get("message", detail)
                except Exception:
                    pass
                raise HTTPException(status_code=response.status_code, detail=detail)
            
            repos = response.json()
            return [
                {
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "clone_url": r.get("clone_url"),
                    "description": r.get("description"),
                    "private": r.get("private"),
                }
                for r in repos if isinstance(r, dict)
            ]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting to GitHub API: {str(e)}"
        )


# ── Admin Endpoints ───────────────────────────────────────────────────────────

@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    """Create a new template and permanently link it to the uploading seller's account."""
    service = TemplateService(db)
    return await service.create_template(data, seller_id=current_user.id)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_seller_or_admin),
):
    """Update an existing template."""
    service = TemplateService(db)
    return await service.update_template(template_id, data)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    """Delete a template. Admins can delete any template; sellers can only delete their own."""
    service = TemplateService(db)
    await service.delete_template(template_id, current_user)


@router.post("/{template_id}/download")
async def download_template(
    template_id: uuid.UUID,
    format: Optional[str] = "zip",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate secure download URL for a purchased template.
    """
    from app.repositories.template_repo import TemplateRepository
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    await template_repo.increment_downloads(template_id)
    
    from app.models.download import Download
    download_log = Download(
        user_id=current_user.id,
        template_id=template_id,
    )
    db.add(download_log)
    await db.flush()
    await db.commit()
    
    download_assets = template.download_assets or {}
    zip_url = download_assets.get("zip")
    if not zip_url:
        raise HTTPException(status_code=400, detail="Source zip file not configured for this template")
        
    return {"download_url": zip_url}
