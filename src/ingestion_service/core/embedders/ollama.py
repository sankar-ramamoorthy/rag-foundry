# src/ingestion_service/core/embedders/ollama.py
import requests


class OllamaEmbedder:
    """
    Embedder using Ollama API.
    """

    dimension = 768  # Ollama model output dimension

    def __init__(self, base_url: str, model: str, batch_size: int = 50):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        """
        try:
            payload = {"model": self.model, "texts": texts}
            response = requests.post(f"{self.base_url}/embeddings", json=payload)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama embedding failed "
                    f"(status={response.status_code}): {response.text}"
                )
            result = response.json()
            # Assume API returns list of embeddings
            return result["embeddings"]
        except Exception as e:
            # In dev/test, fallback or re-raise for visibility
            raise RuntimeError(f"Ollama embedder error: {e}") from e
