"""
Reviews routes.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.review_repo import ReviewRepository
from app.repositories.template_repo import TemplateRepository
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.schemas.common import PaginatedResponse
from math import ceil

router = APIRouter()


@router.get("/template/{template_id}", response_model=PaginatedResponse[ReviewResponse])
async def get_template_reviews(
    template_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated reviews for a template."""
    repo = ReviewRepository(db)
    reviews, total = await repo.get_by_template(template_id, page, page_size)
    return PaginatedResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 1,
    )


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a review for a template. One review per user per template."""
    repo = ReviewRepository(db)

    # Check for duplicate
    existing = await repo.get_user_review_for_template(current_user.id, data.template_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this template",
        )

    # Check if verified purchase (basic check — could be enhanced)
    is_verified = False  # TODO: check orders table in Phase 2

    review = await repo.create(current_user.id, data, is_verified)

    # Update template rating
    avg, count = await repo.get_rating_stats(data.template_id)
    template_repo = TemplateRepository(db)
    await template_repo.update_rating(data.template_id, avg, count)

    return ReviewResponse.model_validate(review)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: uuid.UUID,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update your own review."""
    repo = ReviewRepository(db)
    review = await repo.get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit another user's review")

    review = await repo.update(review, data)

    # Recalculate rating
    avg, count = await repo.get_rating_stats(review.template_id)
    template_repo = TemplateRepository(db)
    await template_repo.update_rating(review.template_id, avg, count)

    return ReviewResponse.model_validate(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete your own review."""
    repo = ReviewRepository(db)
    review = await repo.get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id and current_user.role.value not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Cannot delete another user's review")

    template_id = review.template_id
    await repo.delete(review)

    avg, count = await repo.get_rating_stats(template_id)
    template_repo = TemplateRepository(db)
    await template_repo.update_rating(template_id, avg, count)
