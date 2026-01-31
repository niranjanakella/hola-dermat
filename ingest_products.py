"""Script to ingest products from JSON into Qdrant vector database."""
import json
import os
import sys
from pathlib import Path
from qdrant_client.models import PointStruct
from database.qdrant_client import get_client
from database.collections import initialize_collections, get_embedding
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_products(json_path: str) -> list[dict]:
    """Load products from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_product_text(product: dict) -> str:
    """Create searchable text from product data."""
    text_parts = [
        product.get('name', ''),
        product.get('brand', ''),
        product.get('description', ''),
        product.get('product_type', ''),
        ', '.join(product.get('skin_type_compatibility', [])),
        ', '.join(product.get('key_benefits', [])),
    ]
    
    # Add ingredients (now a list)
    ingredients = product.get('ingredients', [])
    if isinstance(ingredients, list):
        text_parts.append(', '.join(ingredients))
    else:
        # Fallback for old format (shouldn't happen with new data)
        text_parts.append(str(ingredients))
    
    return ' '.join(text_parts)

def ingest_products(products: list[dict], client) -> None:
    """Ingest products into Qdrant."""
    collection_name = settings.PRODUCTS_COLLECTION
    points = []
    
    for product in products:
        # Create searchable text
        product_text = create_product_text(product)
        
        # Generate embedding
        embedding = get_embedding(product_text)
        
        # Create point with metadata
        point = PointStruct(
            id=hash(product['id']) % (2**63),  # Convert to int64
            vector=embedding,
            payload={
                'id': product['id'],
                'name': product['name'],
                'brand': product['brand'],
                'description': product['description'],
                'product_type': product['product_type'],
                'skin_type_compatibility': product['skin_type_compatibility'],
                'regions_available': product['regions_available'],
                'price_range': product['price_range'],
                'usage': product['usage'],
                'key_benefits': product['key_benefits'],
                'ingredients': product['ingredients'],
                'text': product_text,  # Store text for hybrid search
            }
        )
        points.append(point)
    
    # Upsert points
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    logger.info(f"Ingested {len(points)} products into '{collection_name}' collection")

def main():
    """Main ingestion function."""
    # Get script directory
    script_dir = Path(__file__).parent
    json_path = script_dir / 'products.json'
    
    if not json_path.exists():
        logger.error(f"Products file not found: {json_path}")
        sys.exit(1)
    
    # Initialize collections
    logger.info("Initializing collections...")
    initialize_collections()
    
    # Load products
    logger.info(f"Loading products from {json_path}...")
    products = load_products(str(json_path))
    logger.info(f"Loaded {len(products)} products")
    
    # Ingest products
    client = get_client()
    logger.info("Ingesting products into Qdrant...")
    ingest_products(products, client)
    
    logger.info("Product ingestion completed successfully!")

if __name__ == "__main__":
    main()
