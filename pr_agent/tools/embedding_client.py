import json
import logging
from typing import List

import requests


class EmbeddingClientError(Exception):
    pass


class EmbeddingClient:
    def __init__(self, base_url: str, model: str, api_key: str | None = None, timeout_sec: int = 30):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_sec = timeout_sec

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not self.base_url:
            raise EmbeddingClientError("Embedding base URL is required")
        if not texts:
            return []

        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=self.timeout_sec,
            )
        except requests.RequestException as exc:
            raise EmbeddingClientError(f"Embedding request failed: {exc}") from exc

        if response.status_code >= 400:
            raise EmbeddingClientError(
                f"Embedding request failed: {response.status_code} {response.text}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise EmbeddingClientError("Embedding response was not valid JSON") from exc

        embeddings = self._extract_embeddings(data)
        if len(embeddings) != len(texts):
            logging.getLogger(__name__).warning(
                "Embedding count mismatch: expected %s, got %s",
                len(texts),
                len(embeddings),
            )
        return embeddings

    @staticmethod
    def _extract_embeddings(data: object) -> List[List[float]]:
        if isinstance(data, dict) and "data" in data:
            return [item["embedding"] for item in data.get("data", []) if "embedding" in item]
        if isinstance(data, list):
            return [
                item["embedding"] if isinstance(item, dict) and "embedding" in item else item
                for item in data
            ]
        raise EmbeddingClientError("Unexpected embedding response format")
