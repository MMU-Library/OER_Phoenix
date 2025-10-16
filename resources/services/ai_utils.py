from sentence_transformers import SentenceTransformer
from django.db.models import F
from pgvector.django import L2Distance
from resources.models import OERResource
import numpy as np

model = None

def get_embedding_model():
    global model
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

def generate_embeddings(batch_size=50):
    model = get_embedding_model()
    resources = OERResource.objects.filter(embedding__isnull=True)
    
    for i in range(0, resources.count(), batch_size):
        batch = resources[i:i+batch_size]
        texts = [f"{r.title} {r.description}" for r in batch]
        embeddings = model.encode(texts, show_progress_bar=True)
        
        for resource, embedding in zip(batch, embeddings):
            resource.embedding = embedding.tolist()
            resource.save()
