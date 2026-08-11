from typing import Annotated

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.models.place import Place

COLLECTION_NAME = "places"
EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small


class QdrantClientWrapper:
    """Client for Qdrant vector database operations."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: str | None = None,
        collection_name: str = COLLECTION_NAME,
    ):
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_place(
        self, place: Place, embedding: list[float], payload: dict
    ) -> None:
        point = PointStruct(
            id=place.id,
            vector=embedding,
            payload=payload,
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 50,
        query_filter: models.Filter | None = None,
    ) -> list[dict]:
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    def search_batch(
        self,
        query_vectors: list[list[float]],
        limit: int = 50,
    ) -> list[list[dict]]:
        results = self.client.search_batch(
            collection_name=self.collection_name,
            requests=[
                models.SearchRequest(
                    vector=vec,
                    limit=limit,
                )
                for vec in query_vectors
            ],
        )
        return [
            [
                {"id": hit.id, "score": hit.score, "payload": hit.payload}
                for hit in batch
            ]
            for batch in results
        ]

    def delete_place(self, place_id: str) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=[place_id]),
        )

    def count(self) -> int:
        return self.client.get_collection(self.collection_name).points_count
