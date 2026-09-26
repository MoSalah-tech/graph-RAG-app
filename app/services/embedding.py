from langchain_voyageai import VoyageAIEmbeddings
from app.core.config import settings

def get_embeddings() -> VoyageAIEmbeddings:
    """
    Returns a Voyage AI embedding model.

    voyage-4: 1024-dimensional, balanced general-purpose model.
    Runs in the cloud — nothing is downloaded locally.
    """
    return VoyageAIEmbeddings(
        voyage_api_key=settings.VOYAGE_API_KEY,
        model=settings.EMBEDDING_MODEL,
    )