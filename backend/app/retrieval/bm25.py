"""BM25 keyword search implementation."""

import re
from typing import Callable
from rank_bm25 import BM25Okapi


class BM25Searcher:
    """BM25-based keyword search for places."""

    def __init__(self, places: list[dict] | None = None):
        self.places: list[dict] = []
        self.corpus: list[str] = []
        self.bm25: BM25Okapi | None = None
        if places:
            self.index(places)

    def index(self, places: list[dict]) -> None:
        """Build BM25 index from places."""
        self.places = places
        self.corpus = [self._tokenize(self._place_to_text(p)) for p in places]
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)

    def _place_to_text(self, place: dict) -> str:
        """Convert place to searchable text."""
        parts = [
            place.get("name", ""),
            place.get("description", ""),
            place.get("category", ""),
            place.get("subcategory", ""),
            place.get("address", ""),
        ]
        return " ".join(filter(None, parts))

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenizer - lowercase and split on non-alphanumeric."""
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        return tokens

    def search(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        """Search for places matching query. Returns list of (index, score)."""
        if not self.bm25:
            return []

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k results with their scores
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        return [(i, scores[i]) for i in top_indices if scores[i] > 0]

    def search_places(self, query: str, top_k: int = 50) -> list[dict]:
        """Search and return place objects with scores."""
        results = self.search(query, top_k)
        return [
            {
                "place": self.places[idx],
                "score": score,
                "index": idx,
            }
            for idx, score in results
        ]
