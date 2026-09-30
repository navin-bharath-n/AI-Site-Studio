"""
Dashboard routes — user-facing stats and data aggregation.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.download import Download
from app.models.template import Template

from app.core.redis import cache_get, cache_set
from app.models.wishlist import WishlistItem
from app.models.favorite import Favorite

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return aggregated stats for the current user's dashboard with Redis caching."""
    cache_key = f"user:{current_user.id}:stats"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    # Execute all 5 counts in ONE single unified SQL query via scalar subqueries
    combined_query = select(
        select(func.count(Order.id))
        .where(Order.user_id == current_user.id, Order.status == OrderStatus.COMPLETED)
        .scalar_subquery()
        .label("purchases"),

        select(func.count(Download.id))
        .where(Download.user_id == current_user.id)
        .scalar_subquery()
        .label("downloads"),

        select(func.count(WishlistItem.id))
        .where(WishlistItem.user_id == current_user.id)
        .scalar_subquery()
        .label("wishlist"),

        select(func.count(Favorite.id))
        .where(Favorite.user_id == current_user.id)
        .scalar_subquery()
        .label("favorites"),

        select(func.count(Template.id))
        .where(Template.seller_id == current_user.id)
        .scalar_subquery()
        .label("uploaded_templates"),
    )

    res = await db.execute(combined_query)
    row = res.first()

    stats = {
        "purchases": row.purchases if row else 0,
        "downloads": row.downloads if row else 0,
        "wishlist": row.wishlist if row else 0,
        "favorites": row.favorites if row else 0,
        "uploaded_templates": row.uploaded_templates if row else 0,
    }

    await cache_set(cache_key, stats, ttl=60)
    return stats
