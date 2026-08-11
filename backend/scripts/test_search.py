"""Test script for the retrieval pipeline."""

import json
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.retrieval.embedder import Embedder
from app.retrieval.bm25 import BM25Searcher
from app.retrieval.hybrid import HybridSearcher
from app.retrieval.reranker import Reranker
from app.models.preferences import UserPreferences


def load_places():
    """Load places from seed data."""
    seed_file = Path(__file__).parent.parent / "seed_data" / "tokyo_places.json"
    with open(seed_file) as f:
        return json.load(f)


def test_bm25_search():
    """Test BM25 search only."""
    print("=" * 50)
    print("Testing BM25 Search")
    print("=" * 50)

    places = load_places()
    searcher = BM25Searcher()
    searcher.index(places)

    queries = ["temple shrine", "sushi ramen", "shopping luxury", "observation tower"]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = searcher.search(query, top_k=5)
        for i, (idx, score) in enumerate(results[:5], 1):
            place = places[idx]
            print(f"  {i}. {place['name']} (score: {score:.3f})")


def test_hybrid_search():
    """Test hybrid search (BM25 only without Qdrant)."""
    print("\n" + "=" * 50)
    print("Testing Hybrid Search (BM25 only)")
    print("=" * 50)

    places = load_places()
    embedder = Embedder()
    searcher = HybridSearcher(embedder, qdrant_client=None)
    searcher.index_places(places)

    queries = ["cultural attractions", "foodie dining", "modern Tokyo"]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = searcher.search(query, top_k=5)
        for i, result in enumerate(results[:5], 1):
            place = result["place"]
            print(f"  {i}. {place['name']} ({place['category']}) - rrf: {result['rrf_score']:.3f}")


def test_reranker():
    """Test reranker with preferences."""
    print("\n" + "=" * 50)
    print("Testing Reranker")
    print("=" * 50)

    places = load_places()
    embedder = Embedder()
    searcher = HybridSearcher(embedder, qdrant_client=None)
    searcher.index_places(places)
    reranker = Reranker()

    preferences = UserPreferences(
        destination="Tokyo",
        days=3,
        people=2,
        budget=100000,
        categories=["attraction", "restaurant"],
        style="cultural",
    )

    # Search and rerank
    results = searcher.search("Tokyo things to do", top_k=10)
    reranked = reranker.rerank(results, preferences=preferences)

    print(f"\nQuery: 'Tokyo things to do'")
    print(f"Preferences: style={preferences.style}, categories={preferences.categories}")
    print("\nTop 5 after reranking:")
    for i, result in enumerate(reranked[:5], 1):
        place = result["place"]
        print(f"  {i}. {place['name']} ({place['category']})")
        print(f"      final: {result['final_score']:.3f} = "
              f"rrf: {result['rrf_score']:.3f} + "
              f"pref: {result['preference_score']:.2f} + "
              f"balance: {result['balance_score']:.2f}")


def main():
    test_bm25_search()
    test_hybrid_search()
    test_reranker()
    print("\n" + "=" * 50)
    print("All tests complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
