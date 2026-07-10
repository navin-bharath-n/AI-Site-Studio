import uuid
import httpx
import json
import os
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import settings
import logging
logger = logging.getLogger(__name__)
from app.repositories.template_repo import TemplateRepository
from app.schemas.template import TemplateCardResponse, TemplateFilterParams


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_repo = TemplateRepository(db)
        self._qdrant: Optional[AsyncQdrantClient] = None

    @property
    def qdrant(self) -> AsyncQdrantClient:
        if not self._qdrant:
            url = settings.QDRANT_URL
            # If Qdrant URL is local and not active, or not specified, fall back to local disk persistence
            if url and "localhost" not in url and "127.0.0.1" not in url:
                self._qdrant = AsyncQdrantClient(
                    url=url,
                    api_key=settings.QDRANT_API_KEY or None,
                )
            else:
                db_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "qdrant_storage"
                )
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Using local disk-based Qdrant persistence at: {db_dir}")
                self._qdrant = AsyncQdrantClient(path=db_dir)
        return self._qdrant


    async def _get_gemini_embedding(self, text: str) -> List[float]:
        """Generate dense vector embedding using Gemini text-embedding-004 API."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")

        headers = {"Content-Type": "application/json"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_EMBEDDING_MODEL}:embedContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
            "content": {
                "parts": [{"text": text}]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                return data["embedding"]["values"]
            else:
                raise RuntimeError(f"Gemini Embedding API returned {response.status_code}: {response.text}")

    async def _ensure_collection(self) -> None:
        """Verify if Qdrant collection exists and has 3072 dimensions; recreate if mismatch."""
        try:
            info = await self.qdrant.get_collection(settings.QDRANT_COLLECTION)
            vectors_config = info.config.params.vectors
            
            # Extract size safely
            current_size = 0
            if hasattr(vectors_config, "size"):
                current_size = vectors_config.size
            elif isinstance(vectors_config, dict) and "size" in vectors_config:
                current_size = vectors_config["size"]
                
            if current_size != 3072:
                logger.info(f"Recreating Qdrant collection {settings.QDRANT_COLLECTION} with 3072 dimensions...")
                await self.qdrant.delete_collection(settings.QDRANT_COLLECTION)
                await self.qdrant.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=qdrant_models.VectorParams(
                        size=3072,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
        except Exception:
            logger.info(f"Creating Qdrant collection {settings.QDRANT_COLLECTION} (3072 dimensions)...")
            await self.qdrant.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=qdrant_models.VectorParams(
                    size=3072,
                    distance=qdrant_models.Distance.COSINE
                )
            )



    async def _rank_templates(self, query: str, templates_data: List[dict]) -> List[uuid.UUID]:
        """Use RankGemini (gemini-3.5-flash) to re-rank the templates based on query relevance."""
        if not settings.GEMINI_API_KEY or not templates_data:
            return [t["id"] for t in templates_data]

        # Format templates list for LLM context
        formatted_list = []
        for i, t in enumerate(templates_data):
            tags_str = ", ".join(t.get("tags", []))
            formatted_list.append(
                f"Index: {i}\nID: {t['id']}\nTitle: {t['title']}\nDescription: {t['description']}\nTags: {tags_str}\nIndustry: {t.get('industry', '')}\nStyle: {t.get('style', '')}\nColor: {t.get('color_scheme', '')}\n---"
            )
        templates_str = "\n".join(formatted_list)

        prompt = f"""
You are a highly precise search reranking engine.
Given the user's search query: "{query}"

Analyze the following list of templates and rank them from MOST relevant to LEAST relevant to the query.

Templates list:
{templates_str}

Return the results ONLY as a JSON list of the template UUID strings in order of relevance. Do not include markdown code block notation (like ```json ... ```), explanations, or comments.
Example format:
[
  "0cabb02f-7a07-4349-b1c9-b9987348bbb1",
  "d6b9d628-9774-4b53-a75d-6c178229b47e"
]
"""
        headers = {"Content-Type": "application/json"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=20.0)
                if response.status_code == 200:
                    data = response.json()
                    text_response = data["candidates"][0]["content"]["parts"][0]["text"].strip()

                    if text_response.startswith("```json"):
                        text_response = text_response.replace("```json", "", 1)
                    if text_response.endswith("```"):
                        text_response = text_response[:-3]
                    
                    ranked_ids = json.loads(text_response.strip())
                    return [uuid.UUID(rid) for rid in ranked_ids]
                else:
                    logger.error(f"RankGemini API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"RankGemini failed: {e}")

        # Fallback to the similarity search retrieved order if LLM reranking fails
        return [t["id"] for t in templates_data]

    async def keyword_search(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> List[TemplateCardResponse]:
        """Full-text keyword search using PostgreSQL ILIKE."""
        filters = TemplateFilterParams(q=query, page=page, page_size=page_size)
        templates, _ = await self.template_repo.list_with_filters(filters)
        return [TemplateCardResponse.model_validate(t) for t in templates]

    async def semantic_search(
        self, query: str, limit: int = 20, category_filter: Optional[str] = None
    ) -> List[TemplateCardResponse]:
        """
        Semantic search using Gemini embeddings + Qdrant similarity + RankGemini LLM Reranking.

        1. Embed the query with Gemini text-embedding-004 API.
        2. Query Qdrant for top 30 nearest matches.
        3. Re-rank top 30 matches using RankGemini.
        4. Return top 10 results from PostgreSQL in ranked order.
        """
        if not settings.GEMINI_API_KEY:
            return await self.keyword_search(query, page_size=limit)

        try:
            # Step 1: Embed the query
            query_vector = await self._get_gemini_embedding(query)

            # Step 2: Query Qdrant (pull top 30 for reranking)
            search_filter = None
            if category_filter:
                search_filter = qdrant_models.Filter(
                    must=[qdrant_models.FieldCondition(key="category", match=qdrant_models.MatchValue(value=category_filter))]
                )

            # Ensure collection is correctly initialized
            await self._ensure_collection()

            results = await self.qdrant.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=30,  # Grab candidate set of 30 for reranker
                query_filter=search_filter,
            )

            if not results:
                return []

            # Prepare list of candidates for RankGemini
            candidates = []
            for r in results:
                if r.payload:
                    candidates.append({
                        "id": uuid.UUID(r.payload["template_id"]),
                        "title": r.payload.get("title", ""),
                        "description": r.payload.get("description", ""),
                        "tags": r.payload.get("tags", []),
                        "industry": r.payload.get("industry", ""),
                        "style": r.payload.get("style", ""),
                        "color_scheme": r.payload.get("color_scheme", "")
                    })

            # Step 3: Re-rank using RankGemini
            ranked_ids = await self._rank_templates(query, candidates)
            # Slice to final requested limit (usually top 10)
            final_ids = ranked_ids[:limit]

            # Step 4: Fetch templates from PostgreSQL
            templates = await self.template_repo.get_by_ids(final_ids)
            id_to_template = {t.id: t for t in templates}

            return [
                TemplateCardResponse.model_validate(id_to_template[tid])
                for tid in final_ids
                if tid in id_to_template
            ]

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return await self.keyword_search(query, page_size=limit)

    async def index_template(self, template_id: uuid.UUID, text: str, metadata: dict) -> str:
        """
        Embed a template using Gemini text-embedding-004 and index it in Qdrant.
        Combines Name, Category, Industry, Description, Tags, Features, Framework, Style, and Colors.
        """
        if not settings.GEMINI_API_KEY:
            return str(template_id)

        # Build detailed document text for optimal embedding quality
        title = metadata.get("title", "")
        category = metadata.get("category", "")
        industry = metadata.get("industry", "")
        tags = metadata.get("tags", [])
        features = metadata.get("features", [])
        framework = metadata.get("framework", "")
        style = metadata.get("style", "")
        color_scheme = metadata.get("color_scheme", "")
        seo_keywords = metadata.get("seo_keywords", [])

        doc_parts = [
            f"Template Name: {title}",
            f"Category: {category}",
            f"Industry: {industry}",
            f"Description: {text}",
            f"Framework: {framework}",
            f"Style: {style}",
            f"Color Theme: {color_scheme}",
            f"Tags: {', '.join(tags)}" if tags else "",
            f"Features: {', '.join(features)}" if features else "",
            f"SEO Keywords: {', '.join(seo_keywords)}" if seo_keywords else ""
        ]
        doc_text = "\n".join([p for p in doc_parts if p])

        # Get vector embedding from Gemini
        vector = await self._get_gemini_embedding(doc_text)

        # Ensure collection is correctly initialized
        await self._ensure_collection()

        point_id = str(template_id)
        # Store metadata matching the keys parsed in RankGemini
        payload = {
            "template_id": point_id,
            "title": title,
            "category": category,
            "industry": industry,
            "description": text,
            "tags": tags,
            "features": features,
            "framework": framework,
            "style": style,
            "color_scheme": color_scheme,
            "seo_keywords": seo_keywords
        }

        await self.qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=[qdrant_models.PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id

