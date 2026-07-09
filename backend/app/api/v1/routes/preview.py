"""
Preview routes — create preview sessions and serve watermarked previews.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.models.user import User
from app.services.preview_service import PreviewService
from app.services.ai_service import ai_service
from app.repositories.template_repo import TemplateRepository
from pydantic import BaseModel

router = APIRouter()


class PreviewRequest(BaseModel):
    template_id: uuid.UUID
    business_name: str
    industry: str
    primary_color: Optional[str] = "#6366f1"
    secondary_color: Optional[str] = "#8b5cf6"
    about: Optional[str] = None
    services: Optional[list] = None
    contact: Optional[dict] = None
    location: Optional[str] = None
    social_links: Optional[dict] = None
    logo_url: Optional[str] = None
    ai_fill: bool = False  # If True, auto-generate content via AI


class PreviewResponse(BaseModel):
    session_id: uuid.UUID
    preview_image_url: Optional[str] = None
    business_data: dict
    generated_content: Optional[dict] = None
    template_id: uuid.UUID


@router.post("", response_model=PreviewResponse)
async def create_preview(
    request: PreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Create a watermarked live preview session.

    If `ai_fill=true`, AI generates the business content automatically.
    Returns a watermarked preview image URL + session ID.
    """
    service = PreviewService(db)
    template_repo = TemplateRepository(db)

    template = await template_repo.get_by_id(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    business_data = {
        "business_name": request.business_name,
        "industry": request.industry,
        "primary_color": request.primary_color,
        "secondary_color": request.secondary_color,
        "about": request.about,
        "services": request.services or [],
        "contact": request.contact or {},
        "location": request.location,
        "social_links": request.social_links or {},
        "logo_url": request.logo_url,
    }

    generated_content = None
    if request.ai_fill and ai_service.client:
        try:
            generated_content = await ai_service.generate_business_content(
                business_name=request.business_name,
                industry=request.industry,
                template_type=template.category.name if template.category else "business",
            )
            # Merge AI content into business_data
            business_data.update(generated_content)
        except Exception:
            pass  # AI fill optional — continue without it

    user_email = current_user.email if current_user else None

    session = await service.create_session(
        template_id=request.template_id,
        business_data=business_data,
        user_email=user_email,
        is_ai_filled=request.ai_fill,
    )

    # Generate watermarked preview
    preview_url = None
    try:
        preview_url = await service.generate_preview_screenshot(
            session_id=session.id,
            template_thumbnail_url=template.thumbnail_url,
            user_email=user_email,
        )
        session.preview_image_url = preview_url
        session.generated_content = generated_content
        await db.flush()
    except Exception:
        pass  # Preview image is optional — session is still created

    return PreviewResponse(
        session_id=session.id,
        preview_image_url=preview_url,
        business_data=business_data,
        generated_content=generated_content,
        template_id=request.template_id,
    )


@router.get("/{session_id}", response_model=PreviewResponse)
async def get_preview_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve an existing preview session by ID."""
    from sqlalchemy import select
    from app.models.preview_session import PreviewSession

    result = await db.execute(
        select(PreviewSession).where(PreviewSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Preview session not found")

    return PreviewResponse(
        session_id=session.id,
        preview_image_url=session.preview_image_url,
        business_data=session.business_data or {},
        generated_content=session.generated_content,
        template_id=session.template_id,
    )


# Global locks to prevent parallel builds of the same template
_build_locks = {}


@router.get("/live/{template_id}", response_class=Response)
@router.get("/live/{template_id}/{filepath:path}", response_class=Response)
async def serve_live_preview(
    template_id: uuid.UUID,
    request: Request,
    filepath: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Redirect to URL with trailing slash to ensure relative assets load correctly in browser
    if not filepath and not request.url.path.endswith("/"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=str(request.url) + "/")
    """
    Dynamically extract, compile (if needed), and serve the template's actual frontend code in the browser as a running live demo.
    """
    import os
    import zipfile
    import io
    import mimetypes
    import asyncio
    import platform
    import subprocess
    import tempfile
    from fastapi.responses import Response
    from sqlalchemy import select
    from app.repositories.template_repo import TemplateRepository
    
    template_repo = TemplateRepository(db)
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    download_assets = template.download_assets or {}
    zip_url = download_assets.get("zip")
    if not zip_url:
        raise HTTPException(status_code=400, detail="Template does not have source ZIP assets")
        
    file_id_str = zip_url.split("/")[-1]
    try:
        file_id = uuid.UUID(file_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source asset URL")
        
    preview_dir = os.path.join(tempfile.gettempdir(), "ai_site_studio", "live_previews", str(template_id))
    os.makedirs(preview_dir, exist_ok=True)
    
    # Extract files if preview_dir is empty (first-time extract)
    if not os.listdir(preview_dir):
        from app.models import StoredFile
        result = await db.execute(select(StoredFile).where(StoredFile.id == file_id))
        stored_file = result.scalar_one_or_none()
        if not stored_file:
            raise HTTPException(status_code=404, detail="Source template archive file not found")
            
        with zipfile.ZipFile(io.BytesIO(stored_file.data)) as zip_ref:
            for member in zip_ref.infolist():
                clean_path = os.path.normpath(member.filename).replace("..", "")
                if clean_path.startswith("/") or clean_path.startswith("\\"):
                    clean_path = clean_path[1:]
                    
                target_path = os.path.join(preview_dir, clean_path)
                if member.is_dir():
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(zip_ref.read(member.filename))

    # Detect package.json to see if this is a Node.js project requiring compilation
    package_json_path = None
    for root, dirs, files in os.walk(preview_dir):
        if "package.json" in files:
            package_json_path = os.path.join(root, "package.json")
            break

    serve_root = preview_dir
    build_dir = None

    if package_json_path:
        project_root = os.path.dirname(package_json_path)
        build_folders = ["dist", "out", "build", ".output", "public"]
        
        # Check if project is already compiled
        for d in build_folders:
            candidate = os.path.join(project_root, d)
            if os.path.isdir(candidate):
                # Search for index.html recursively inside build folder (e.g. dist/index.html)
                for b_root, b_dirs, b_files in os.walk(candidate):
                    if "index.html" in b_files:
                        build_dir = b_root
                        break
                if build_dir:
                    break

        # If not compiled, trigger compilation
        if not build_dir:
            lock = _build_locks.setdefault(template_id, asyncio.Lock())
            async with lock:
                # Check again under lock in case another request compiled it
                for d in build_folders:
                    candidate = os.path.join(project_root, d)
                    if os.path.isdir(candidate):
                        for b_root, b_dirs, b_files in os.walk(candidate):
                            if "index.html" in b_files:
                                build_dir = b_root
                                break
                        if build_dir:
                            break
                
                if not build_dir:
                    # Run compilation
                    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
                    loop = asyncio.get_running_loop()
                    
                    # 1. npm install
                    def run_npm_install():
                        return subprocess.run(
                            [npm_cmd, "install", "--no-audit", "--no-fund"],
                            cwd=project_root,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                    
                    install_res = await loop.run_in_executor(None, run_npm_install)
                    if install_res.returncode != 0:
                        print(f"npm install failed for {template_id}: {install_res.stderr.decode('utf-8', errors='ignore')}")
                    
                    # 2. npm run build
                    def run_npm_build():
                        return subprocess.run(
                            [npm_cmd, "run", "build"],
                            cwd=project_root,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                    build_res = await loop.run_in_executor(None, run_npm_build)
                    if build_res.returncode != 0:
                        print(f"npm run build failed for {template_id}: {build_res.stderr.decode('utf-8', errors='ignore')}")
                        
                    # Locate build dir again after build
                    for d in build_folders:
                        candidate = os.path.join(project_root, d)
                        if os.path.isdir(candidate):
                            for b_root, b_dirs, b_files in os.walk(candidate):
                                if "index.html" in b_files:
                                    build_dir = b_root
                                    break
                            if build_dir:
                                break

        if build_dir:
            serve_root = build_dir
        else:
            serve_root = project_root

    # Locate index.html
    index_file_path = os.path.join(serve_root, "index.html")
    if not os.path.exists(index_file_path):
        for root, dirs, files in os.walk(serve_root):
            if "index.html" in files:
                index_file_path = os.path.join(root, "index.html")
                serve_root = root
                break

    # Determine file to serve
    if not filepath or filepath == "/":
        full_path = index_file_path
    else:
        safe_path = os.path.normpath(filepath).replace("..", "")
        if safe_path.startswith("/") or safe_path.startswith("\\"):
            safe_path = safe_path[1:]
        full_path = os.path.join(serve_root, safe_path)
        
        # Fallback for nested layouts if not found directly
        if not os.path.exists(full_path):
            subdirs = [d for d in os.listdir(serve_root) if os.path.isdir(os.path.join(serve_root, d)) and d not in ["__MACOSX"]]
            if len(subdirs) == 1:
                nested_path = os.path.join(serve_root, subdirs[0], safe_path)
                if os.path.exists(nested_path):
                    full_path = nested_path

    if not os.path.exists(full_path) or os.path.isdir(full_path):
        # Fallback to index.html if file not found (e.g. client side routing)
        if os.path.exists(index_file_path):
            full_path = index_file_path
        else:
            raise HTTPException(status_code=404, detail="Requested file not found in template")
            
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = "application/octet-stream"
        
    with open(full_path, "rb") as f:
        content = f.read()

    # Rewrite absolute references to relative on index.html (helpful for subpath hosting on local dev)
    if mime_type == "text/html" and filepath in [None, "", "/"]:
        try:
            html_content = content.decode("utf-8", errors="ignore")
            # Replace absolute links /assets/, /css/, /js/, /img/ with relative versions
            for folder in ["assets", "css", "js", "img", "fonts", "static"]:
                html_content = html_content.replace(f'src="/{folder}/', f'src="./{folder}/')
                html_content = html_content.replace(f'href="/{folder}/', f'href="./{folder}/')
                html_content = html_content.replace(f'src=\'/{folder}/', f'src=\'./{folder}/')
                html_content = html_content.replace(f'href=\'/{folder}/', f'href=\'./{folder}/')
            content = html_content.encode("utf-8")
        except Exception:
            pass
        
    return Response(content=content, media_type=mime_type)
