"""Qdrant collection setup and management."""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    CollectionStatus,
    OptimizersConfigDiff,
    HnswConfigDiff,
)
from sentence_transformers import SentenceTransformer
from database.qdrant_client import get_client
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Initialize embedding model
embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
EMBEDDING_DIM = embedding_model.get_sentence_embedding_dimension()

def get_embedding(text: str) -> list[float]:
    """Generate embedding for text."""
    return embedding_model.encode(text).tolist()

def create_products_collection(client: QdrantClient) -> None:
    """Create the products collection with ACORN configuration."""
    collection_name = settings.PRODUCTS_COLLECTION
    
    # Check if collection exists
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        logger.info(f"Collection '{collection_name}' already exists")
        return
    
    # Create collection with ACORN-optimized configuration
    # Qdrant v1.16+ automatically uses ACORN for filtered searches
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
        optimizers_config=OptimizersConfigDiff(
            # ACORN works best with these optimizer settings
            indexing_threshold=10000,
        ),
        hnsw_config=HnswConfigDiff(
            # HNSW parameters for better search performance
            m=16,
            ef_construct=100,
        ),
    )
    logger.info(f"Created collection '{collection_name}' with {EMBEDDING_DIM}D vectors")

def create_history_collection(client: QdrantClient) -> None:
    """Create the history collection for user interactions."""
    collection_name = settings.HISTORY_COLLECTION
    
    # Check if collection exists
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        logger.info(f"Collection '{collection_name}' already exists")
        return
    
    # Create collection for user history
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
        optimizers_config=OptimizersConfigDiff(
            indexing_threshold=10000,
        ),
        hnsw_config=HnswConfigDiff(
            m=16,
            ef_construct=100,
        ),
    )
    logger.info(f"Created collection '{collection_name}' with {EMBEDDING_DIM}D vectors")

def initialize_collections() -> None:
    """Initialize all collections."""
    client = get_client()
    create_products_collection(client)
    create_history_collection(client)
    logger.info("All collections initialized")
