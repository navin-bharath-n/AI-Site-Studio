"""
Search service — keyword + semantic (OpenAI Embeddings + Qdrant) search.
"""

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import SearchRequest, Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.repositories.template_repo import TemplateRepository
from app.schemas.template import TemplateCardResponse, TemplateFilterParams


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_repo = TemplateRepository(db)
        self._openai: Optional[AsyncOpenAI] = None
        self._qdrant: Optional[AsyncQdrantClient] = None

    @property
    def openai(self) -> AsyncOpenAI:
        if not self._openai:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    @property
    def qdrant(self) -> AsyncQdrantClient:
        if not self._qdrant:
            self._qdrant = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
            )
        return self._qdrant

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
        Semantic search using OpenAI embeddings + Qdrant vector similarity.

        1. Embed the query with text-embedding-3-small
        2. Search Qdrant for nearest neighbors
        3. Fetch matching templates from PostgreSQL
        """
        if not settings.OPENAI_API_KEY:
            # Fallback to keyword search if OpenAI is not configured
            return await self.keyword_search(query, page_size=limit)

        # Step 1: Generate query embedding
        embedding_response = await self.openai.embeddings.create(
            input=query,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
        query_vector = embedding_response.data[0].embedding

        # Step 2: Query Qdrant
        search_filter = None
        if category_filter:
            search_filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value=category_filter))]
            )

        try:
            results = await self.qdrant.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
            )
            template_ids = [uuid.UUID(r.payload["template_id"]) for r in results if r.payload]
        except Exception:
            # Qdrant not available — fallback to keyword search
            return await self.keyword_search(query, page_size=limit)

        if not template_ids:
            return []

        # Step 3: Fetch from PostgreSQL
        templates = await self.template_repo.get_by_ids(template_ids)
        # Preserve Qdrant ranking order
        id_to_template = {t.id: t for t in templates}
        return [
            TemplateCardResponse.model_validate(id_to_template[tid])
            for tid in template_ids
            if tid in id_to_template
        ]

    async def index_template(self, template_id: uuid.UUID, text: str, metadata: dict) -> str:
        """
        Embed a template description and upsert into Qdrant.
        Called when a template is created or updated.

        Returns the Qdrant point ID (same as str(template_id)).
        """
        if not settings.OPENAI_API_KEY:
            return str(template_id)

        embedding_response = await self.openai.embeddings.create(
            input=text,
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
        vector = embedding_response.data[0].embedding

        from qdrant_client.http.models import PointStruct
        point_id = str(template_id)
        metadata["template_id"] = point_id

        await self.qdrant.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=[PointStruct(id=point_id, vector=vector, payload=metadata)],
        )
        return point_id
