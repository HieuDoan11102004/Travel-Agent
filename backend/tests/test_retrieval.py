"""Tests for retrieval pipeline."""

import pytest
from unittest.mock import MagicMock, patch

from app.retrieval.bm25 import BM25Searcher
from app.retrieval.embedder import Embedder
from app.retrieval.reranker import Reranker
from app.retrieval.hybrid import HybridSearcher


# Sample places for testing
SAMPLE_PLACES = [
    {
        "id": "place-001",
        "name": "Senso-ji Temple",
        "category": "attraction",
        "subcategory": "temple",
        "location": {"lat": 35.7148, "lng": 139.7967},
        "cost_estimate": 0,
        "duration_hours": 2,
        "popularity": "high",
        "rating": 4.7,
        "description": "Tokyo's oldest temple",
    },
    {
        "id": "place-002",
        "name": "Tokyo Skytree",
        "category": "attraction",
        "subcategory": "observation_tower",
        "location": {"lat": 35.7101, "lng": 139.8107},
        "cost_estimate": 3100,
        "duration_hours": 2.5,
        "popularity": "high",
        "rating": 4.5,
        "description": "Tallest tower in Japan",
    },
    {
        "id": "place-003",
        "name": "Sukiyabashi Jiro",
        "category": "restaurant",
        "subcategory": "sushi",
        "location": {"lat": 35.6736, "lng": 139.7639},
        "cost_estimate": 30000,
        "duration_hours": 1.5,
        "popularity": "high",
        "rating": 4.8,
        "description": "World-renowned sushi restaurant",
    },
    {
        "id": "place-004",
        "name": "Ginza Shopping District",
        "category": "shopping",
        "subcategory": "luxury",
        "location": {"lat": 35.6715, "lng": 139.7649},
        "cost_estimate": 10000,
        "duration_hours": 3,
        "popularity": "high",
        "rating": 4.5,
        "description": "Upscale shopping district",
    },
]


class TestBM25Searcher:
    def test_index_places(self):
        searcher = BM25Searcher()
        searcher.index(SAMPLE_PLACES)
        assert len(searcher.places) == 4
        assert len(searcher.corpus) == 4

    def test_search_temple(self):
        searcher = BM25Searcher()
        searcher.index(SAMPLE_PLACES)
        results = searcher.search("temple shrine", top_k=5)
        assert len(results) > 0
        assert results[0][0] == 0  # Senso-ji should be first

    def test_search_sushi(self):
        searcher = BM25Searcher()
        searcher.index(SAMPLE_PLACES)
        results = searcher.search("sushi restaurant", top_k=5)
        assert len(results) > 0
        assert results[0][0] == 2  # Sukiyabashi Jiro

    def test_search_empty_index(self):
        searcher = BM25Searcher()
        results = searcher.search("anything", top_k=5)
        assert results == []


class TestEmbedder:
    def test_embed_place_text(self):
        embedder = Embedder()
        text = embedder.embed_place(SAMPLE_PLACES[0])
        assert "Senso-ji Temple" in text
        assert "Tokyo's oldest temple" in text
        assert "attraction" in text

    @patch("app.retrieval.embedder.OpenAI")
    def test_embed_text_mock(self, mock_openai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        embedder = Embedder()
        embedder._client = mock_client
        result = embedder.embed_text("test query")

        assert len(result) == 1536
        mock_client.embeddings.create.assert_called_once()


class TestReranker:
    def test_rerank_basic(self):
        reranker = Reranker()
        results = [
            {"place": SAMPLE_PLACES[0], "score": 1.0},
            {"place": SAMPLE_PLACES[2], "score": 0.8},
        ]
        reranked = reranker.rerank(results)
        assert len(reranked) == 2
        assert "final_score" in reranked[0]

    def test_rerank_with_preferences(self):
        reranker = Reranker()
        from app.models.preferences import UserPreferences

        prefs = UserPreferences(
            destination="Tokyo",
            days=2,
            people=1,
            budget=50000,
            categories=["restaurant", "attraction"],
        )

        results = [
            {"place": SAMPLE_PLACES[3], "score": 0.3},  # shopping (lower score, not in categories)
            {"place": SAMPLE_PLACES[2], "score": 0.6},  # restaurant (matches category)
            {"place": SAMPLE_PLACES[0], "score": 0.5},  # attraction (matches category)
        ]
        reranked = reranker.rerank(results, preferences=prefs)
        # Shopping should be last (lower base score + not matching categories)
        assert reranked[-1]["place"]["id"] == "place-004"

    def test_category_balance(self):
        reranker = Reranker()
        results = [
            {"place": SAMPLE_PLACES[0], "score": 0.5},  # attraction (first seen)
            {"place": SAMPLE_PLACES[0], "score": 0.5},  # attraction (already seen, lower balance)
            {"place": SAMPLE_PLACES[2], "score": 0.51},  # restaurant (new category)
        ]
        reranked = reranker.rerank(results, balance_categories=True)
        # Restaurant should rank higher due to better category balance score
        assert reranked[0]["place"]["id"] == "place-003"


class TestHybridSearcher:
    def test_init(self):
        embedder = Embedder()
        searcher = HybridSearcher(embedder)
        assert searcher.embedder is embedder
        assert searcher.rrf_k == 60

    def test_index_places(self):
        embedder = Embedder()
        searcher = HybridSearcher(embedder, qdrant_client=None)
        searcher.index_places(SAMPLE_PLACES)
        assert len(searcher.bm25.places) == 4

    def test_search_without_qdrant(self):
        """Test BM25-only search when Qdrant unavailable."""
        embedder = Embedder()
        searcher = HybridSearcher(embedder, qdrant_client=None)
        searcher.index_places(SAMPLE_PLACES)

        results = searcher.search("temple", top_k=5)
        assert len(results) > 0
        assert results[0]["place"]["id"] == "place-001"

    def test_category_filter(self):
        embedder = Embedder()
        searcher = HybridSearcher(embedder, qdrant_client=None)
        searcher.index_places(SAMPLE_PLACES)

        results = searcher.search("Tokyo", category_filter="restaurant", top_k=5)
        for r in results:
            assert r["place"]["category"] == "restaurant"

    def test_rrf_fusion(self):
        embedder = Embedder()
        searcher = HybridSearcher(embedder, qdrant_client=None)
        searcher.index_places(SAMPLE_PLACES)

        # Search for "sushi" - BM25 will find restaurant, no vector results
        results = searcher.search("sushi", top_k=5)
        assert len(results) > 0
        assert "rrf_score" in results[0]
