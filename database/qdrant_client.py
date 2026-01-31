"""Qdrant client initialization and management."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config.settings import settings
import os

# Initialize disk-based Qdrant client
VECTORDB_PATH = "./vectordb"
os.makedirs(VECTORDB_PATH, exist_ok=True)
client = QdrantClient(path=VECTORDB_PATH)

def get_client() -> QdrantClient:
    """Get the Qdrant client instance."""
    return client
