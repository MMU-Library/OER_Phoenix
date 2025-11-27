"""
Centralized AI/vector helpers for Open Educational Resourcer.

Configuration (via `.env` or Django settings):
    EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2          # or any compatible HF repo/id/path
    VECTOR_BACKEND=pgvector                        # or 'qdrant'
    QDRANT_URL=http://qdrant:6333

All model and vector DB access should use these helpers!
"""

import os
from resources.models import OERResource

# Singleton pattern for model & vector client
_MODEL = None
_VECTOR_CLIENT = None

def get_embedding_model():
    global _MODEL
    if _MODEL is None:
        # Model name is now configurable!
        from sentence_transformers import SentenceTransformer
        model_name = os.environ.get('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
        _MODEL = SentenceTransformer(model_name)
    return _MODEL

def get_vector_db_client():
    """
    Switchable vector DB client: 'pgvector' (direct, recommended default),
    'qdrant' (via HTTP API), or others.
    """
    global _VECTOR_CLIENT
    backend = os.environ.get('VECTOR_BACKEND', 'pgvector').lower()
    if backend == 'qdrant':
        if _VECTOR_CLIENT is None:
            from qdrant_client import QdrantClient
            qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
            _VECTOR_CLIENT = QdrantClient(url=qdrant_url)
        return _VECTOR_CLIENT
    # For 'pgvector' backend, the Django ORM and VectorField are used directly.
    return None

def generate_embeddings(batch_size=50):
    """
    Compute and store embeddings for all OERResources missing one.
    Only uses the embedding model (vector DB indexing handled elsewhere).
    """
    model = get_embedding_model()
    qs = OERResource.objects.filter(content_embedding__isnull=True)

    total = qs.count()
    for start in range(0, total, batch_size):
        batch = list(qs[start:start + batch_size])
        texts = [f"{r.title} {r.description or ''}" for r in batch]
        embeddings = model.encode(texts, show_progress_bar=False)
        for resource, emb in zip(batch, embeddings):
            try:
                resource.content_embedding = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
                resource.save()
            except Exception:
                continue
    # (Optional: index in Qdrant if that's the configured backend)
    if os.environ.get('VECTOR_BACKEND', 'pgvector') == 'qdrant':
        client = get_vector_db_client()
        # TODO: implement batch upsert to Qdrant if desired

def compute_and_store_embedding_for_resource(resource_id):
    """
    Compute and store embedding for a single resource.
    If using external vector DB (e.g. Qdrant), index as well.
    """
    try:
        resource = OERResource.objects.get(id=resource_id)
    except OERResource.DoesNotExist:
        return False

    model = get_embedding_model()
    text = f"{resource.title} {resource.description or ''}"
    emb = model.encode([text])[0]
    try:
        resource.content_embedding = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
        resource.save()
        if os.environ.get('VECTOR_BACKEND', 'pgvector') == 'qdrant':
            client = get_vector_db_client()
            # TODO: upsert just this record in Qdrant here
        return True
    except Exception:
        return False

# ---- (Optional: helper for test/demonstration) ----
def embed_and_index_all_resources():
    """
    Utility: (Re-)embed and optionally (re-)index ALL resources.
    """
    generate_embeddings()
    if os.environ.get('VECTOR_BACKEND', 'pgvector') == 'qdrant':
        client = get_vector_db_client()
        # TODO: implement full (re-)index if Qdrant or another external DB is used.
