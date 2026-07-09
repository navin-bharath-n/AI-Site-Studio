import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.storage import storage
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/{file_id}")
async def get_stored_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Stream a file from PostgreSQL storage."""
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")

    result = await storage.get_file(db, file_uuid)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")

    data, content_type, original_filename = result
    headers = {}
    if original_filename:
        headers["Content-Disposition"] = f'inline; filename="{original_filename}"'

    return Response(content=data, media_type=content_type, headers=headers)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Store an uploaded file and return its public URL."""
    # 1. Early check using content length / metadata if available
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    if file.size and file.size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 2. Read in chunks to prevent loading huge files into memory (OOM safety)
    content = b""
    chunk_size = 1024 * 1024  # 1MB chunks
    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            content += chunk
            if len(content) > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB."
                )
    finally:
        await file.close()

    url = await storage.upload_file(
        db=db,
        file_content=content,
        folder="uploads",
        original_filename=file.filename,
        content_type=file.content_type,
    )
    return {"url": url}
