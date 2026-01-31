"""Qdrant tools for product search, history search, and history updates."""
from typing import List, Dict, Any, Optional
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    MatchText,
    MatchAny,
    Range,
)
from database.qdrant_client import get_client
from database.collections import get_embedding, settings
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

def search_products(
    query_text: str,
    skin_type: Optional[str] = None,
    regions: Optional[List[str]] = None,
    usage: Optional[str] = None,
    required_ingredients: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search products using semantic and keyword search with ACORN filtering.
    
    Args:
        query_text: Natural language query describing desired products
        skin_type: Filter by compatible skin type
        regions: Filter by regions where product is available
        usage: Filter by usage time (morning/night/both)
        required_ingredients: List of required ingredient keywords
        limit: Maximum number of results
    
    Returns:
        List of matching products with metadata
    """
    try:
        client = get_client()
        collection_name = settings.PRODUCTS_COLLECTION
        
        # Generate query embedding
        query_embedding = get_embedding(query_text)
        
        # Build ACORN filter conditions
        filter_conditions = []
        
        if skin_type:
            filter_conditions.append(
                FieldCondition(
                    key="skin_type_compatibility",
                    match=MatchValue(value=skin_type)
                )
            )
        
        if regions:
            # Product must be available in at least one of the specified regions
            # Use 'should' logic: at least one region match
            filter_conditions.append(
                Filter(
                    should=[
                        FieldCondition(
                            key="regions_available",
                            match=MatchValue(value=region)
                        )
                        for region in regions
                    ]
                )
            )
        
        if usage:
            filter_conditions.append(
                FieldCondition(
                    key="usage",
                    match=MatchValue(value=usage)
                )
            )
        
        if required_ingredients:
            # Check if any required ingredient is present in the ingredients list
            # Create conditions for each required ingredient
            # MatchValue on array fields checks if the value exists in the array
            ingredient_conditions = []
            for ingredient in required_ingredients:
                # Try exact match first
                ingredient_normalized = ingredient.lower().strip()
                ingredient_conditions.append(
                    FieldCondition(
                        key="ingredients",
                        match=MatchValue(value=ingredient_normalized)
                    )
                )
                # Also try original case
                ingredient_conditions.append(
                    FieldCondition(
                        key="ingredients",
                        match=MatchValue(value=ingredient.strip())
                    )
                )
            if ingredient_conditions:
                # Use 'should' logic: at least one ingredient must match
                filter_conditions.append(
                    Filter(should=ingredient_conditions)
                )
        
        # Create filter (ACORN will handle complex filtering)
        query_filter = None
        if filter_conditions:
            # Separate simple conditions from nested filters
            simple_conditions = []
            nested_filters = []
            
            for condition in filter_conditions:
                if isinstance(condition, Filter):
                    nested_filters.append(condition)
                else:
                    simple_conditions.append(condition)
            
            # Build final filter
            if nested_filters and simple_conditions:
                # Combine both: must have simple conditions AND (at least one nested filter match)
                query_filter = Filter(
                    must=simple_conditions + nested_filters
                )
            elif simple_conditions:
                query_filter = Filter(must=simple_conditions)
            elif nested_filters:
                # If only nested filters, use should logic
                if len(nested_filters) == 1:
                    query_filter = nested_filters[0]
                else:
                    query_filter = Filter(should=nested_filters)
        
        # Perform hybrid search (semantic + keyword)
        # Qdrant v1.16+ ACORN algorithm handles zero-result scenarios automatically
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=0.3,  # Minimum similarity threshold
            with_payload=True,
            with_vectors=False
        )
        
        # Also perform keyword search on text field
        keyword_results = []
        if query_text:
            try:
                keyword_results = client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="text",
                                match=MatchText(text=query_text)
                            )
                        ] + (filter_conditions if filter_conditions else [])
                    ),
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )[0]
            except Exception as e:
                logger.warning(f"Keyword search failed: {e}")
        
        # Combine and deduplicate results
        products = []
        seen_ids = set()
        
        # Add semantic search results
        for point in results:
            if point.id not in seen_ids:
                products.append({
                    "id": point.payload.get("id"),
                    "name": point.payload.get("name"),
                    "brand": point.payload.get("brand"),
                    "description": point.payload.get("description"),
                    "product_type": point.payload.get("product_type"),
                    "skin_type_compatibility": point.payload.get("skin_type_compatibility", []),
                    "regions_available": point.payload.get("regions_available", []),
                    "price_range": point.payload.get("price_range"),
                    "usage": point.payload.get("usage"),
                    "key_benefits": point.payload.get("key_benefits", []),
                    "ingredients": point.payload.get("ingredients", []),
                    "score": point.score
                })
                seen_ids.add(point.id)
        
        # Add keyword search results
        for point in keyword_results:
            if point.id not in seen_ids:
                products.append({
                    "id": point.payload.get("id"),
                    "name": point.payload.get("name"),
                    "brand": point.payload.get("brand"),
                    "description": point.payload.get("description"),
                    "product_type": point.payload.get("product_type"),
                    "skin_type_compatibility": point.payload.get("skin_type_compatibility", []),
                    "regions_available": point.payload.get("regions_available", []),
                    "price_range": point.payload.get("price_range"),
                    "usage": point.payload.get("usage"),
                    "key_benefits": point.payload.get("key_benefits", []),
                    "ingredients": point.payload.get("ingredients", {}),
                    "score": 0.5  # Default score for keyword matches
                })
                seen_ids.add(point.id)
        
        logger.info(f"Found {len(products)} products matching query")
        return products[:limit]
        
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        return []

def search_user_history(
    user_id: str,
    query_text: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Retrieve user's historical interactions and product usage.
    
    Args:
        user_id: Unique user identifier
        query_text: Optional query to search within history
        limit: Maximum number of results
    
    Returns:
        List of historical interactions
    """
    try:
        client = get_client()
        collection_name = settings.HISTORY_COLLECTION
        
        filter_conditions = [
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id)
            )
        ]
        
        query_filter = Filter(must=filter_conditions)
        
        if query_text:
            # Semantic search within user's history
            query_embedding = get_embedding(query_text)
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            history_items = [
                {
                    "timestamp": point.payload.get("timestamp"),
                    "interaction_type": point.payload.get("interaction_type"),
                    "product_id": point.payload.get("product_id"),
                    "product_name": point.payload.get("product_name"),
                    "feedback": point.payload.get("feedback"),
                    "results": point.payload.get("results"),
                    "rating": point.payload.get("rating"),
                    "score": point.score
                }
                for point in results
            ]
        else:
            # Get all user history, sorted by timestamp
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )[0]
            
            history_items = [
                {
                    "timestamp": point.payload.get("timestamp"),
                    "interaction_type": point.payload.get("interaction_type"),
                    "product_id": point.payload.get("product_id"),
                    "product_name": point.payload.get("product_name"),
                    "feedback": point.payload.get("feedback"),
                    "results": point.payload.get("results"),
                    "rating": point.payload.get("rating")
                }
                for point in results
            ]
            # Sort by timestamp descending (most recent first)
            history_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        logger.info(f"Retrieved {len(history_items)} history items for user {user_id}")
        return history_items
        
    except Exception as e:
        logger.error(f"Error searching user history: {str(e)}")
        return []

def update_user_history(
    user_id: str,
    interaction_type: str,
    product_id: Optional[str] = None,
    product_name: Optional[str] = None,
    feedback: Optional[str] = None,
    results: Optional[str] = None,
    rating: Optional[int] = None
) -> bool:
    """
    Store user interaction in history collection.
    
    Args:
        user_id: Unique user identifier
        interaction_type: Type of interaction (recommendation, feedback, purchase, etc.)
        product_id: Product identifier (optional)
        product_name: Product name (optional)
        feedback: User feedback text (optional)
        results: Results/outcomes from using the product (optional)
        rating: Numeric rating 1-5 (optional)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        collection_name = settings.HISTORY_COLLECTION
        
        # Create text for embedding
        history_text_parts = [
            interaction_type,
            product_name or "",
            feedback or "",
            results or ""
        ]
        history_text = " ".join(history_text_parts)
        
        # Generate embedding
        embedding = get_embedding(history_text)
        
        # Create payload
        payload = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "interaction_type": interaction_type,
            "product_id": product_id,
            "product_name": product_name,
            "feedback": feedback,
            "results": results,
            "rating": rating,
            "text": history_text
        }
        
        # Generate unique point ID
        point_id = hash(f"{user_id}_{datetime.now().isoformat()}_{uuid.uuid4()}") % (2**63)
        
        # Upsert point
        from qdrant_client.models import PointStruct
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        
        client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        
        logger.info(f"Updated history for user {user_id}: {interaction_type}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user history: {str(e)}")
        return False

def add_product_to_collection(product: Dict[str, Any]) -> bool:
    """
    Add a new product to the Qdrant products collection.
    
    Args:
        product: Product dictionary with fields:
            - id: Product identifier
            - name: Product name
            - brand: Brand name
            - description: Product description
            - ingredients: List of ingredients
            - product_type: Type of product (serum, moisturizer, etc.)
            - skin_type_compatibility: List of compatible skin types
            - regions_available: List of regions where available
            - price_range: Price range ($, $$, $$$, $$$$)
            - usage: Usage timing (morning/night/both)
            - key_benefits: List of key benefits
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()
        collection_name = settings.PRODUCTS_COLLECTION
        
        # Create searchable text (similar to ingest_products.py)
        text_parts = [
            product.get('name', ''),
            product.get('brand', ''),
            product.get('description', ''),
            product.get('product_type', ''),
            ', '.join(product.get('skin_type_compatibility', [])),
            ', '.join(product.get('key_benefits', [])),
        ]
        
        # Add ingredients
        ingredients = product.get('ingredients', [])
        if isinstance(ingredients, list):
            text_parts.append(', '.join(ingredients))
        
        product_text = ' '.join(text_parts)
        
        # Generate embedding
        embedding = get_embedding(product_text)
        
        # Create point with metadata
        from qdrant_client.models import PointStruct
        point = PointStruct(
            id=hash(product.get('id', str(uuid.uuid4()))) % (2**63),
            vector=embedding,
            payload={
                'id': product.get('id', f"prod_{uuid.uuid4().hex[:8]}"),
                'name': product.get('name', ''),
                'brand': product.get('brand', ''),
                'description': product.get('description', ''),
                'product_type': product.get('product_type', ''),
                'skin_type_compatibility': product.get('skin_type_compatibility', []),
                'regions_available': product.get('regions_available', []),
                'price_range': product.get('price_range', '$$'),
                'usage': product.get('usage', 'both'),
                'key_benefits': product.get('key_benefits', []),
                'ingredients': product.get('ingredients', []),
                'text': product_text,
            }
        )
        
        # Upsert point
        client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        
        logger.info(f"Added product '{product.get('name')}' to collection")
        return True
        
    except Exception as e:
        logger.error(f"Error adding product to collection: {str(e)}")
        return False
