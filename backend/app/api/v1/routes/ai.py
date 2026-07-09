"""
AI routes — content generation, SEO, color palettes, template recommendations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.ai_service import ai_service

router = APIRouter()


class ContentGenerateRequest(BaseModel):
    business_name: str
    industry: str
    template_type: str = "business"
    additional_context: Optional[str] = None


class SEORequest(BaseModel):
    business_name: str
    industry: str
    services: List[str]
    location: Optional[str] = None


class ColorPaletteRequest(BaseModel):
    industry: str
    mood: str = "professional"


class RecommendRequest(BaseModel):
    description: str
    available_categories: List[str]


@router.post("/generate-content")
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate website content for a business using GPT."""
    result = await ai_service.generate_business_content(
        business_name=request.business_name,
        industry=request.industry,
        template_type=request.template_type,
        additional_context=request.additional_context,
    )
    return result


@router.post("/generate-seo")
async def generate_seo(
    request: SEORequest,
    current_user: User = Depends(get_current_user),
):
    """Generate SEO meta tags and keywords."""
    return await ai_service.generate_seo(
        business_name=request.business_name,
        industry=request.industry,
        services=request.services,
        location=request.location,
    )


@router.post("/color-palette")
async def generate_color_palette(
    request: ColorPaletteRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a color palette for a business."""
    return await ai_service.generate_color_palette(
        industry=request.industry,
        mood=request.mood,
    )


@router.post("/recommend")
async def recommend_templates(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
):
    """Get AI-powered template category recommendations based on business description."""
    return await ai_service.recommend_templates(
        user_description=request.description,
        available_categories=request.available_categories,
    )
