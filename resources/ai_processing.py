"""
Retrieval helpers: Qdrant-backed retriever with NumPy fallback.

This module prefers Qdrant when available (fast ANN search at scale). If
`qdrant_client` is not installed or Qdrant is not reachable, it falls
back to a simple in-memory NumPy cosine-similarity retriever (suitable
only for small demos).
"""

import os
import logging
from typing import List, Tuple
import numpy as np
from resources.models import OERResource
from resources.services.ai_utils import get_embedding_model

logger = logging.getLogger(__name__)

def _as_np(x) -> np.ndarray:
    """
    Safely convert input to a NumPy array.

    Handles:
    - PyTorch tensors
    - List of numbers or lists
    - Other array-like objects

    Returns:
        A 1D or 2D NumPy array with float32 dtype
    """
    if hasattr(x, "cpu"):  # PyTorch tensor
        return x.cpu().numpy().astype(np.float32)
    elif isinstance(x, np.ndarray):
        return x.astype(np.float32)
    elif isinstance(x, list):
        # Convert nested lists recursively
        def _convert(item):
            if isinstance(item, list):
                return [_convert(sub_item) for sub_item in item]
            else:
                return float(item)
        converted = _convert(x)
        return np.array(converted, dtype=np.float32)
    else:
        # Fallback for other types (e.g., scalars, sparse arrays)
        try:
            arr = np.asarray(x, dtype=np.float32)
            return arr
        except Exception as e:
            raise ValueError(f"Failed to convert input to NumPy array: {str(e)}") from e

class BaseRetriever:
    def get_similar_resources(self, query: str, k: int = 5) -> List[Tuple[OERResource, float]]:
        raise NotImplementedError()

class QdrantRetriever(BaseRetriever):
    """
    Qdrant-backed retriever using `qdrant-client`.

    Stores vectors in a Qdrant collection named `oer_resources` and keeps
    useful metadata as payload for quick retrieval.
    """

    COLLECTION = os.environ.get('QDRANT_COLLECTION', 'oer_resources')

    def __init__(self, host: str | None = None, port: int = 6333):
        try:
            from qdrant_client import QdrantClient  # type: ignore
        except Exception as e:
            raise RuntimeError("qdrant-client not installed") from e

        host = host or os.environ.get('QDRANT_HOST', 'qdrant')
        url = f"http://{host}:{port}"

        try:
            self.client = QdrantClient(url=url)
            _ = self.client.get_collections()
        except Exception as e:
            raise RuntimeError(f"unable to connect to Qdrant at {url}: {e}") from e

    def reindex(self, batch_size: int = 500):
        from qdrant_client.http import models as rest_models  # type: ignore

        qs = OERResource.objects.filter(content_embedding__isnull=False)
        points = []
        for r in qs.iterator():
            vec = _as_np(r.content_embedding)
            if vec is None:
                continue
            payload = {
                'title': r.title,
                'url': r.url,
                'source': getattr(r.source, 'name', None),
                'resource_id': getattr(r, 'pk', None),
            }
            points.append(
                rest_models.PointStruct(
                    id=int(getattr(r, 'pk', 0)),
                    vector=vec.tolist(),  # Always store as list to Qdrant!
                    payload=payload
                )
            )
            if len(points) >= batch_size:
                self.client.upsert(collection_name=self.COLLECTION, points=points)
                points = []
        if points:
            self.client.upsert(collection_name=self.COLLECTION, points=points)

def get_similar_resources(self, query: str, k: int = 5):
    try:
        model = get_embedding_model()
        q_emb = model.encode([query])[0]
        q_vec = _as_np(q_emb)  # Always convert embedding to NumPy then to list
        if q_vec is None:
            return []

        # FIX: Use 'search' for points query
        hits = self.client.search(
            collection_name=self.COLLECTION,
            query_vector=q_vec.tolist(),
            limit=k
        )

        results = []
        ids = [int(h.id) for h in hits]
        resources = {r.pk: r for r in OERResource.objects.filter(pk__in=ids)}
        for h in hits:
            r = resources.get(int(h.id))
            score = float(h.score) if hasattr(h, 'score') else 0.0
            if r:
                results.append((r, score))
        return results
    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []

class NumpyInMemoryRetriever(BaseRetriever):
    """
    Fallback retriever that loads db vectors into memory and does linear scan.

    Suitable for small datasets and demos only.
    """

    def __init__(self):
        self.embedding_model = None
        self.index = []

    def build_vector_store(self, force=False):
        if self.index and not force:
            return
        self.index = []
        qs = OERResource.objects.filter(content_embedding__isnull=False, is_active=True)
        for r in qs:
            vec = _as_np(r.content_embedding)
            if vec is None:
                continue
            self.index.append((r, vec))

    def reindex(self, batch_size: int = 500):
        self.build_vector_store(force=True)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def get_similar_resources(self, query: str, k: int = 5):
        if not self.index:
            self.build_vector_store()
        if not self.index:
            return []
        if self.embedding_model is None:
            try:
                self.embedding_model = get_embedding_model()
            except Exception:
                logger.exception('Failed to load embedding model for in-memory retriever')
                return []

        try:
            q_emb = self.embedding_model.encode([query])[0]
            q_vec = _as_np(q_emb)
            if q_vec is None:
                return []
        except Exception:
            return []

        scores = []
        for resource, vec in self.index:
            score = self._cosine_similarity(q_vec, vec)
            scores.append((resource, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

def get_retriever(preferred: str = 'qdrant') -> BaseRetriever:
    """Factory that returns a retriever. Tries preferred backend, falls back.

    preferred: 'qdrant' or 'numpy'
    """
    if preferred == 'qdrant':
        try:
            return QdrantRetriever()
        except Exception:
            logger.info('Qdrant not available, falling back to in-memory retriever')
            return NumpyInMemoryRetriever()
    return NumpyInMemoryRetriever()
