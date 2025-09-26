"""
Reusable vector search tool shared by agents.
"""
import logging
from typing import Any, Dict, List, Optional

from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class VectorSearchTool:
    """Reusable vector search utility for agents.

    Performs vector similarity search and returns both raw chunks and
    formatted strings suitable for summarization and citation.
    """

    def __init__(self, max_tokens_per_source: int = 1000, chars_per_token: int = 4) -> None:
        self.max_tokens_per_source = max_tokens_per_source
        self.chars_per_token = chars_per_token

    async def search(
        self,
        *,
        query: str,
        document_id: Optional[str],
        top_k: int,
        similarity_threshold: float,
        max_tokens_per_source: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute vector search and format outputs.

        Args:
            query: Natural language query.
            document_id: Restrict search to a document if provided.
            top_k: Number of chunks to retrieve.
            similarity_threshold: Minimum similarity threshold.
            max_tokens_per_source: Optional override for per-source token cap.

        Returns:
            Dict with keys:
              - similar_chunks: list of chunk dicts with metadata
              - formatted_results: deduplicated, truncated content string
              - formatted_sources: human-readable sources list
        """
        try:
            logger.info(
                f"VectorSearchTool: searching (top_k={top_k}, threshold={similarity_threshold}) for query: {query[:80]}..."
            )

            similar_chunks = await embedding_service.search_similar_chunks(
                query=query,
                document_id=document_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            token_cap = max_tokens_per_source or self.max_tokens_per_source
            formatted_results = self._deduplicate_and_format_sources(
                similar_chunks, token_cap
            )
            formatted_sources = self._format_sources(similar_chunks)

            return {
                "similar_chunks": similar_chunks,
                "formatted_results": formatted_results,
                "formatted_sources": formatted_sources,
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"VectorSearchTool error: {str(exc)}")
            return {
                "similar_chunks": [],
                "formatted_results": "",
                "formatted_sources": "",
                "error": str(exc),
            }

    def _deduplicate_and_format_sources(
        self, chunks: List[Dict[str, Any]], max_tokens_per_source: int
    ) -> str:
        formatted_sources: List[str] = []
        seen_content: set[str] = set()

        for chunk in chunks:
            content = chunk.get("content", "")
            # Skip if we've seen similar content
            content_preview = content[:100]
            if content_preview in seen_content:
                continue
            seen_content.add(content_preview)

            # Truncate if too long
            max_chars = max_tokens_per_source * self.chars_per_token
            if len(content) > max_chars:
                content = content[:max_chars] + "..."

            # Format the chunk
            page_num = chunk.get("page_number", "Unknown")
            similarity = float(chunk.get("similarity_score", 0))
            formatted_source = f"[Page {page_num} | Similarity: {similarity:.2f}]\n{content}\n"
            formatted_sources.append(formatted_source)

        return "\n---\n".join(formatted_sources)

    def _format_sources(self, chunks: List[Dict[str, Any]]) -> str:
        sources: List[str] = []
        for chunk in chunks:
            page_num = chunk.get("page_number", "Unknown")
            chunk_idx = chunk.get("chunk_index", "Unknown")
            sources.append(f"- Page {page_num}, Chunk {chunk_idx}")
        return "\n".join(sources)


# Singleton instance for convenience
vector_search_tool = VectorSearchTool()

