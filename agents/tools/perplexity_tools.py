"""Perplexity API tools for weather and product research."""
import httpx
import json
from typing import Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def research_weather_atmosphere(
    region: str,
    include_forecast: bool = True,
    days_back: int = 3,
    days_forward: int = 5
) -> Dict[str, Any]:
    """
    Research current and forecasted weather conditions for a region.
    
    Args:
        region: Region name (city, state, country)
        include_forecast: Whether to include future forecast
        days_back: Number of past days to include
        days_forward: Number of future days for forecast
    
    Returns:
        Dictionary with weather data including temperature, UV index, air quality
    """
    try:
        # Construct query for Perplexity
        query = f"""Provide detailed weather and atmospheric conditions for {region}:
        - Current temperature and temperature trends over the past {days_back} days
        - Current UV index and UV index forecast for the next {days_forward} days
        - Current Air Quality Index (AQI) and air quality trends
        - Humidity levels
        - Any relevant environmental factors affecting skin health
        
        Format the response as structured data with specific numerical values where available."""
        
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a weather and environmental data expert. Provide accurate, structured information about weather conditions, UV index, and air quality."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(PERPLEXITY_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract content from response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse structured data from response
            weather_data = {
                "region": region,
                "current_temperature": None,
                "temperature_trend": None,
                "current_uv_index": None,
                "uv_forecast": None,
                "current_aqi": None,
                "air_quality_trend": None,
                "humidity": None,
                "raw_response": content,
                "sources": result.get("citations", [])
            }
            
            # Try to extract structured information from the response
            # The agent will parse this further, but we provide raw data
            logger.info(f"Weather research completed for {region}")
            return weather_data
            
    except Exception as e:
        logger.error(f"Error researching weather for {region}: {str(e)}")
        return {
            "region": region,
            "error": str(e),
            "raw_response": None
        }

def research_regional_products(
    region: str,
    skin_type: Optional[str] = None,
    skin_concerns: Optional[list] = None
) -> Dict[str, Any]:
    """
    Research top skincare products available in a specific region.
    
    Args:
        region: Region name (city, state, country)
        skin_type: User's skin type (optional)
        skin_concerns: List of skin concerns (optional)
    
    Returns:
        Dictionary with product research data
    """
    try:
        # Construct query
        concerns_text = f" for {skin_type} skin" if skin_type else ""
        concerns_text += f" addressing {', '.join(skin_concerns)}" if skin_concerns else ""
        
        query = f"""Research the top-rated and most popular skincare products available in {region}{concerns_text}.
        Include:
        - Product names and brands
        - Where they are available (stores, online retailers)
        - Price ranges
        - Key ingredients and benefits
        - User reviews and ratings
        - Regional availability and popularity
        
        Focus on products that are actually available and accessible in {region}."""
        
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a skincare product research expert. Provide detailed information about product availability, pricing, and effectiveness in specific regions."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(PERPLEXITY_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            product_data = {
                "region": region,
                "skin_type": skin_type,
                "skin_concerns": skin_concerns,
                "raw_response": content,
                "sources": result.get("citations", [])
            }
            
            logger.info(f"Product research completed for {region}")
            return product_data
            
    except Exception as e:
        logger.error(f"Error researching products for {region}: {str(e)}")
        return {
            "region": region,
            "error": str(e),
            "raw_response": None
        }

def research_skin_type_analysis(
    region_origin: str,
    region_stay: str,
    environment_factors: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Research how regional factors affect skin type and needs.
    
    Args:
        region_origin: User's region of origin
        region_stay: Current region of stay
        environment_factors: Dictionary with factors like sun_exposure, screen_time, etc.
    
    Returns:
        Dictionary with skin analysis data
    """
    try:
        factors_text = ", ".join([f"{k}: {v}" for k, v in environment_factors.items()])
        
        query = f"""Analyze how environmental factors affect skin health:
        - Origin region: {region_origin}
        - Current region: {region_stay}
        - Environmental factors: {factors_text}
        
        Provide insights on:
        - How climate differences between origin and current region affect skin
        - Specific skincare needs based on environmental factors
        - Regional skincare practices and recommendations
        - Common skin concerns in {region_stay}
        - Adaptation strategies for skin care"""
        
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a dermatology expert specializing in environmental skin health. Provide detailed analysis of how regional and environmental factors affect skin."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(PERPLEXITY_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            analysis_data = {
                "region_origin": region_origin,
                "region_stay": region_stay,
                "environment_factors": environment_factors,
                "raw_response": content,
                "sources": result.get("citations", [])
            }
            
            logger.info("Skin type analysis research completed")
            return analysis_data
            
    except Exception as e:
        logger.error(f"Error in skin type analysis: {str(e)}")
        return {
            "error": str(e),
            "raw_response": None
        }
