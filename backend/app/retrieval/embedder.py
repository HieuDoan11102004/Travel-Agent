"""OpenAI embeddings service for vector search."""


from langchain_openai import OpenAIEmbeddings
from openai import OpenAI


class Embedder:
    """Service for generating embeddings using OpenAI."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ):
        self.model = model
        self.dimensions = dimensions
        self._client: OpenAI | None = None
        self._langchain_embedder: OpenAIEmbeddings | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI()
        return self._client

    @property
    def langchain_embedder(self) -> OpenAIEmbeddings:
        if self._langchain_embedder is None:
            self._langchain_embedder = OpenAIEmbeddings(
                model=self.model,
                dimensions=self.dimensions,
            )
        return self._langchain_embedder

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions,
        )
        return response.data[0].embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )
        return [item.embedding for item in response.data]

    async def aembed_text(self, text: str) -> list[float]:
        """Async: Generate embedding for a single text."""
        embedding = await self.langchain_embedder.aembed_query(text)
        return embedding

    async def aembed_texts(self, texts: list[str]) -> list[list[float]]:
        """Async: Generate embeddings for multiple texts."""
        embeddings = await self.langchain_embedder.aembed_documents(texts)
        return embeddings

    def embed_place(self, place: dict) -> str:
        """Generate searchable text for a place."""
        parts = [
            place.get("name", ""),
            place.get("description", ""),
            place.get("category", ""),
            place.get("subcategory", ""),
            place.get("address", ""),
        ]
        return " | ".join(filter(None, parts))
