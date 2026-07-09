"""
AI service — OpenAI integration for preview content generation, 
template recommendations, color palettes, and SEO.
"""

import json
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings


class AIService:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if not self._client:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def generate_business_content(
        self,
        business_name: str,
        industry: str,
        template_type: str,
        additional_context: Optional[str] = None,
    ) -> dict:
        """
        Auto-generate website content for a business.
        Used in the Preview Builder when user clicks "AI Fill".

        Returns a dict with: about, services, tagline, contact_placeholder, etc.
        """
        prompt = f"""You are a professional website copywriter.

Generate compelling website content for a {industry} business called "{business_name}".
The website template is a {template_type} type.
{f'Additional context: {additional_context}' if additional_context else ''}

Return a JSON object with these exact fields:
{{
  "tagline": "catchy one-line tagline",
  "about": "2-3 sentence about us paragraph",
  "services": ["Service 1", "Service 2", "Service 3", "Service 4"],
  "service_descriptions": {{
    "Service 1": "One line description",
    "Service 2": "One line description",
    "Service 3": "One line description",
    "Service 4": "One line description"
  }},
  "cta_primary": "Primary call-to-action button text",
  "cta_secondary": "Secondary call-to-action text",
  "hero_headline": "Hero section headline",
  "hero_subheadline": "Hero section subheadline"
}}

Return only valid JSON, no markdown."""

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def generate_seo(
        self,
        business_name: str,
        industry: str,
        services: list,
        location: Optional[str] = None,
    ) -> dict:
        """Generate SEO meta tags and keywords."""
        prompt = f"""Generate SEO metadata for "{business_name}", a {industry} business.
Services: {', '.join(services)}.
{f'Location: {location}' if location else ''}

Return JSON:
{{
  "meta_title": "...",
  "meta_description": "...",
  "keywords": ["kw1", "kw2", ...],
  "og_title": "...",
  "og_description": "..."
}}"""

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    async def generate_color_palette(self, industry: str, mood: str = "professional") -> dict:
        """Generate a color palette for a business."""
        prompt = f"""Generate a professional color palette for a {industry} business with a {mood} mood.

Return JSON:
{{
  "primary": "#HEXCODE",
  "secondary": "#HEXCODE",
  "accent": "#HEXCODE",
  "background": "#HEXCODE",
  "text": "#HEXCODE",
  "rationale": "Brief explanation"
}}"""

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    async def recommend_templates(
        self,
        user_description: str,
        available_categories: list,
    ) -> dict:
        """Suggest template categories and keywords based on user's business description."""
        prompt = f"""A user is looking for a website template. Their description:
"{user_description}"

Available categories: {', '.join(available_categories)}

Return JSON:
{{
  "recommended_categories": ["cat1", "cat2"],
  "search_keywords": ["kw1", "kw2", "kw3"],
  "reasoning": "Brief explanation"
}}"""

        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)


# Module-level singleton
ai_service = AIService()
