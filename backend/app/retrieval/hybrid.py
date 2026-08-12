"""Hybrid search combining BM25 and vector similarity with RRF fusion."""


from app.data.qdrant_client import QdrantClientWrapper
from app.retrieval.bm25 import BM25Searcher
from app.retrieval.embedder import Embedder


class HybridSearcher:
    """Hybrid search combining BM25 + vector similarity using RRF."""

    def __init__(
        self,
        embedder: Embedder,
        qdrant_client: QdrantClientWrapper | None = None,
        rrf_k: int = 60,
    ):
        self.embedder = embedder
        self.qdrant = qdrant_client
        self.bm25 = BM25Searcher()
        self.rrf_k = rrf_k

    def index_places(self, places: list[dict]) -> None:
        """Index places for both BM25 and vector search."""
        # BM25 indexing
        self.bm25.index(places)

        # Vector indexing (if Qdrant available)
        if self.qdrant:
            self._index_vectors(places)

    def _index_vectors(self, places: list[dict]) -> None:
        """Index places into Qdrant."""
        for place in places:
            text = self.embedder.embed_place(place)
            embedding = self.embedder.embed_text(text)
            self.qdrant.upsert_place(
                place_id=place["id"],
                embedding=embedding,
                payload=place,
            )

    def search(
        self,
        query: str,
        top_k: int = 50,
        category_filter: str | None = None,
        categories: list[str] | None = None,
    ) -> list[dict]:
        """Hybrid search with RRF fusion.

        Args:
            query: Search query
            top_k: Number of results to return
            category_filter: Filter by single category
            categories: Filter by list of categories

        Returns:
            List of places with scores, sorted by RRF score
        """
        results_bm25 = self._search_bm25(query, top_k * 2)
        results_vector = self._search_vector(query, top_k * 2)

        # Apply category filters
        if category_filter or categories:
            filter_cats = [category_filter] if category_filter else categories
            results_bm25 = self._filter_by_categories(results_bm25, filter_cats)
            results_vector = self._filter_by_categories(results_vector, filter_cats)

        # Fuse results with RRF
        fused = self._reciprocal_rank_fusion(results_bm25, results_vector)

        return fused[:top_k]

    def _search_bm25(self, query: str, limit: int) -> list[dict]:
        """BM25 keyword search."""
        return self.bm25.search_places(query, limit)

    def _search_vector(self, query: str, limit: int) -> list[dict]:
        """Vector similarity search."""
        if not self.qdrant:
            return []

        query_embedding = self.embedder.embed_text(query)
        raw_results = self.qdrant.search(query_embedding, limit=limit)

        return [
            {
                "place": r["payload"],
                "score": r["score"],
                "index": -1,
            }
            for r in raw_results
        ]

    def _filter_by_categories(
        self, results: list[dict], categories: list[str]
    ) -> list[dict]:
        """Filter results by category."""
        return [
            r for r in results
            if r["place"].get("category") in categories
        ]

    def _reciprocal_rank_fusion(
        self,
        list_a: list[dict],
        list_b: list[dict],
    ) -> list[dict]:
        """Reciprocal Rank Fusion of two result lists.

        RRF score = sum(1 / (k + rank)), where k is a constant (default 60)
        """
        scores: dict[str, float] = {}
        seen: dict[str, dict] = {}

        # Process list A
        for rank, item in enumerate(list_a):
            place_id = item["place"]["id"]
            score = 1.0 / (self.rrf_k + rank + 1)
            scores[place_id] = scores.get(place_id, 0) + score
            seen[place_id] = item

        # Process list B
        for rank, item in enumerate(list_b):
            place_id = item["place"]["id"]
            score = 1.0 / (self.rrf_k + rank + 1)
            scores[place_id] = scores.get(place_id, 0) + score
            seen[place_id] = item

        # Sort by combined RRF score
        sorted_ids = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)

        return [
            {**seen[pid], "rrf_score": scores[pid]}
            for pid in sorted_ids
        ]
