"""
Phase 4: Embedding Service

Generates vector embeddings using Ollama (nomic-embed-text model).
These embeddings enable semantic search capabilities.
"""

import httpx
from typing import List, Optional
import numpy as np


class EmbeddingService:
    """Service for generating text embeddings using Ollama"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "nomic-embed-text:latest"  # 768-dimensional embeddings
        self.dimension = 768

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text string

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector (768 dimensions)
            Returns None if embedding generation fails
        """
        if not text or not text.strip():
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding")

                    # Validate embedding dimensions
                    if embedding and len(embedding) == self.dimension:
                        return embedding
                    else:
                        print(f"⚠ Warning: Unexpected embedding dimension: {len(embedding) if embedding else 0}")
                        return None
                else:
                    print(f"✗ Ollama embedding failed: HTTP {response.status_code}")
                    return None

        except Exception as e:
            print(f"✗ Error generating embedding: {e}")
            return None

    def generate_embedding_sync(self, text: str) -> Optional[List[float]]:
        """
        Synchronous version of generate_embedding

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector (768 dimensions)
        """
        if not text or not text.strip():
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding")

                    if embedding and len(embedding) == self.dimension:
                        return embedding
                    else:
                        print(f"⚠ Warning: Unexpected embedding dimension: {len(embedding) if embedding else 0}")
                        return None
                else:
                    print(f"✗ Ollama embedding failed: HTTP {response.status_code}")
                    return None

        except Exception as e:
            print(f"✗ Error generating embedding: {e}")
            return None

    def prepare_text_for_embedding(self, title: str, content: Optional[str] = None) -> str:
        """
        Prepare text for embedding by combining title and content

        Args:
            title: Mention title
            content: Optional mention content

        Returns:
            Combined text suitable for embedding
        """
        if content:
            # Combine title and content, truncate if too long (to avoid token limits)
            combined = f"{title}\n\n{content}"
            # Truncate to ~1000 characters to stay within token limits
            if len(combined) > 1000:
                combined = combined[:1000] + "..."
            return combined
        else:
            return title

    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (-1 to 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def test_connection(self) -> bool:
        """
        Test connection to Ollama server and verify model is available

        Returns:
            True if connection successful and model available
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test basic connectivity
                response = await client.get(f"{self.ollama_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]

                    if self.model in models:
                        print(f"✓ Ollama connected: {self.ollama_url}")
                        print(f"✓ Model available: {self.model}")
                        return True
                    else:
                        print(f"⚠ Model '{self.model}' not found. Available models: {models}")
                        print(f"  Run: ollama pull {self.model}")
                        return False
                else:
                    print(f"✗ Ollama connection failed: HTTP {response.status_code}")
                    return False

        except Exception as e:
            print(f"✗ Cannot connect to Ollama: {e}")
            print(f"  Make sure Ollama is running at {self.ollama_url}")
            return False


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(ollama_url: str = "http://localhost:11434") -> EmbeddingService:
    """Get or create global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(ollama_url)
    return _embedding_service
