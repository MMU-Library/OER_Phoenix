from resources.models import OERResource

model = None


def get_embedding_model():
    global model
    if model is None:
        # lazy import to avoid heavy imports at module-import time
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model


def generate_embeddings(batch_size=50):
    """Compute and store embeddings into `OERResource.content_embedding`.

    This writes vectors as lists which are compatible with `pgvector.django.VectorField`.
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
                # don't fail the whole batch on a single problematic record
                continue


def compute_and_store_embedding_for_resource(resource_id):
    """Compute a single resource embedding and store it on the model."""
    from resources.models import OERResource
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
        return True
    except Exception:
        return False
