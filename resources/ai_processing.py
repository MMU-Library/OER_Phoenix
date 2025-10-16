from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .models import OERResource
from langchain_huggingface import HuggingFaceEmbeddings

class OERRetriever:
    def __init__(self):
        self.embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.vector_store = None

    def build_vector_store(self):
        resources = OERResource.objects.all()
        documents = []
        metadatas = []
        for resource in resources:
            content = f"Title: {resource.title}\nDescription: {resource.description}"
            metadata = {
                "source": resource.source,
                "license": resource.license,
                "url": resource.url,
                "id": str(resource.id)
            }
            docs = self.text_splitter.split_text(content)
            documents.extend(docs)
            metadatas.extend([metadata] * len(docs))

        if not documents:
            self.vector_store = None
            return

        self.vector_store = Chroma.from_texts(
            texts=documents,
            embedding=self.embedding,
            metadatas=metadatas
        )

    def get_similar_resources(self, query, k=5):
        if not self.vector_store:
            self.build_vector_store()
        if not self.vector_store:
            return []  # No data to search
        results = self.vector_store.similarity_search_with_score(query, k=k)
        output = []
        for doc, score in results:
            output.append((doc, score))  # Return as tuple
        return output
