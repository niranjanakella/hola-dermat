"""CrewAI setup for skincare recommendation workflow."""
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional
from config.settings import settings
from agents.tools.perplexity_tools import (
    research_weather_atmosphere,
    research_regional_products,
    research_skin_type_analysis
)
from agents.tools.qdrant_tools import (
    search_products,
    search_user_history,
    update_user_history,
    add_product_to_collection
)
from utils.user_profile import UserProfile
import logging

logger = logging.getLogger(__name__)

# Initialize Claude Sonnet 4.5 LLM
llm = LLM(
    model="claude-sonnet-4-5",
    api_key=settings.ANTHROPIC_API_KEY
)

class PerplexityWeatherTool(BaseTool):
    """Tool for researching weather and atmospheric conditions."""
    name: str = "Research Weather and Atmosphere"
    description: str = """Research current and forecasted weather conditions including temperature, 
    UV index, and air quality for a specific region. Use this when you need to understand 
    environmental factors affecting skin health."""
    
    def _run(self, region: str, include_forecast: bool = True) -> str:
        """Execute weather research."""
        try:
            result = research_weather_atmosphere(region, include_forecast)
            return f"Weather data for {region}: {result.get('raw_response', 'No data available')}"
        except Exception as e:
            return f"Error researching weather: {str(e)}"

class PerplexityProductResearchTool(BaseTool):
    """Tool for researching regional product availability."""
    name: str = "Research Regional Products"
    description: str = """Research top skincare products available in a specific region. 
    Use this to find products that are actually accessible to the user based on their location."""
    
    def _run(self, region: str, skin_type: Optional[str] = None, skin_concerns: Optional[List[str]] = None) -> str:
        """Execute product research."""
        try:
            result = research_regional_products(region, skin_type, skin_concerns)
            return f"Product research for {region}: {result.get('raw_response', 'No data available')}"
        except Exception as e:
            return f"Error researching products: {str(e)}"

class PerplexitySkinAnalysisTool(BaseTool):
    """Tool for analyzing skin type based on regional factors."""
    name: str = "Analyze Skin Type and Regional Factors"
    description: str = """Analyze how regional and environmental factors affect skin health. 
    Use this to understand how climate differences and environmental conditions impact skincare needs."""
    
    def _run(self, region_origin: str, region_stay: str, environment_factors: Dict[str, Any]) -> str:
        """Execute skin analysis."""
        try:
            result = research_skin_type_analysis(region_origin, region_stay, environment_factors)
            return f"Skin analysis: {result.get('raw_response', 'No data available')}"
        except Exception as e:
            return f"Error analyzing skin: {str(e)}"

class QdrantProductSearchTool(BaseTool):
    """Tool for searching products in Qdrant database."""
    name: str = "Search Products Database"
    description: str = """Search the product database for skincare products matching specific criteria. 
    Use this to find products from our curated database that match user needs, skin type, 
    required ingredients, and regional availability."""
    
    def _run(
        self, 
        query_text: str,
        skin_type: Optional[str] = None,
        regions: Optional[List[str]] = None,
        usage: Optional[str] = None,
        required_ingredients: Optional[List[str]] = None
    ) -> str:
        """Execute product search."""
        try:
            results = search_products(
                query_text, skin_type, regions, usage, required_ingredients, limit=10
            )
            if not results:
                return "No products found matching the criteria."
            
            formatted_results = []
            for product in results:
                formatted_results.append(
                    f"Product: {product['name']} by {product['brand']}\n"
                    f"Type: {product['product_type']}\n"
                    f"Description: {product['description']}\n"
                    f"Usage: {product['usage']}\n"
                    f"Benefits: {', '.join(product['key_benefits'])}\n"
                    f"Price: {product['price_range']}\n"
                )
            return "\n---\n".join(formatted_results)
        except Exception as e:
            return f"Error searching products: {str(e)}"

class QdrantHistorySearchTool(BaseTool):
    """Tool for searching user history."""
    name: str = "Search User History"
    description: str = """Retrieve user's historical product usage, feedback, and results. 
    Use this to understand what products the user has tried before and their experiences with them."""
    
    def _run(self, user_id: str, query_text: Optional[str] = None) -> str:
        """Execute history search."""
        try:
            results = search_user_history(user_id, query_text, limit=20)
            if not results:
                return "No history found for this user."
            
            formatted_results = []
            for item in results:
                formatted_results.append(
                    f"Date: {item.get('timestamp', 'Unknown')}\n"
                    f"Type: {item.get('interaction_type', 'Unknown')}\n"
                    f"Product: {item.get('product_name', 'N/A')}\n"
                    f"Feedback: {item.get('feedback', 'N/A')}\n"
                    f"Results: {item.get('results', 'N/A')}\n"
                    f"Rating: {item.get('rating', 'N/A')}\n"
                )
            return "\n---\n".join(formatted_results)
        except Exception as e:
            return f"Error searching history: {str(e)}"

class QdrantHistoryUpdateTool(BaseTool):
    """Tool for updating user history."""
    name: str = "Update User History"
    description: str = """Store user interactions, product recommendations, feedback, and results 
    in the history database. Always use this after providing recommendations to track what was suggested.
    IMPORTANT: Do NOT show this action to the user - it's a background task."""
    
    def _run(
        self,
        user_id: str,
        interaction_type: str,
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        feedback: Optional[str] = None,
        results: Optional[str] = None,
        rating: Optional[int] = None
    ) -> str:
        """Execute history update."""
        try:
            success = update_user_history(
                user_id, interaction_type, product_id, product_name, feedback, results, rating
            )
            return "History updated successfully" if success else "Failed to update history"
        except Exception as e:
            return f"Error updating history: {str(e)}"

class QdrantAddProductTool(BaseTool):
    """Tool for adding new products to the Qdrant database."""
    name: str = "Add Product to Database"
    description: str = """Add a new skincare product to the product database. Use this when you find 
    a product from Perplexity research that is not in the database. Extract product details including 
    name, brand, description, ingredients, product type, skin type compatibility, regions available, 
    price range, usage timing, and key benefits."""
    
    def _run(self, product: Dict[str, Any]) -> str:
        """Execute product addition."""
        try:
            success = add_product_to_collection(product)
            if success:
                return f"Successfully added product '{product.get('name', 'Unknown')}' to database"
            else:
                return f"Failed to add product '{product.get('name', 'Unknown')}' to database"
        except Exception as e:
            return f"Error adding product: {str(e)}"

def create_skincare_agent() -> Agent:
    """Create the main skincare expert agent."""
    return Agent(
        role='Personalized Skincare Consultant',
        goal='Understand user needs and provide personalized morning and night skincare regimen recommendations based on their skin type, region, environment, and history',
        backstory="""You are an expert dermatologist with deep knowledge of regional skincare practices, 
        environmental factors affecting skin health, and product formulations. You understand how 
        climate, UV exposure, air quality, and lifestyle factors impact skin needs. You have access 
        to a comprehensive product database and can research regional product availability. You always 
        consider the user's history and previous experiences when making recommendations.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=[
            PerplexityWeatherTool(),
            PerplexityProductResearchTool(),
            PerplexitySkinAnalysisTool(),
            QdrantProductSearchTool(),
            QdrantHistorySearchTool(),
            QdrantHistoryUpdateTool(),
            QdrantAddProductTool()
        ]
    )

def create_recommendation_task(agent: Agent, user_profile: UserProfile, user_id: str) -> Task:
    """Create task for generating skincare recommendations."""
    
    profile_dict = user_profile.to_dict()
    
    task_description = f"""Analyze the user's profile and create personalized skincare recommendations.

User Profile:
- Skin Type: {profile_dict.get('skin_type', 'Not specified')}
- Region of Origin: {profile_dict.get('region_origin', 'Not specified')}
- Current Region: {profile_dict.get('region_stay', 'Not specified')}
- Occupation: {profile_dict.get('occupation', 'Not specified')}
- Screen Time: {profile_dict.get('screen_time', 'Not specified')}
- Sun Exposure: {profile_dict.get('sun_exposure', 'Not specified')}
- Skin Concerns: {', '.join(profile_dict.get('skin_concerns', []))}
- Current Products: {', '.join(profile_dict.get('current_products', []))}
- Allergies: {', '.join(profile_dict.get('allergies', []))}
- Budget: {profile_dict.get('budget_range', 'Not specified')}

Your task:
1. First, check the user's history to understand their past product usage and experiences
2. Research current and forecasted weather conditions (temperature, UV index, air quality) for {profile_dict.get('region_stay', 'their region')}
3. Analyze how regional and environmental factors affect their skin needs
4. Search the product database for products matching their needs, considering:
   - Skin type compatibility
   - Regional availability
   - Required ingredients based on their concerns
   - Usage timing (morning/night)
5. If no products are found in the database, use Perplexity to research top products available in {profile_dict.get('region_stay', 'their region')} that match the user's needs
6. For any products found via Perplexity that are not in the database, add them to the database using the Add Product tool
7. Create a comprehensive morning skincare regimen (cleanser, toner, serum, moisturizer, sunscreen)
8. Create a comprehensive night skincare regimen (cleanser, toner, treatment, moisturizer)
9. Explain why each product was chosen and how it addresses their specific needs
10. Silently update the user history with the recommendations (do not mention this action to the user)

Format your response as:
- Morning Regimen: [list products with explanations]
- Night Regimen: [list products with explanations]
- Rationale: [explain the overall approach]

Be specific about product names, brands, and usage instructions."""
    
    return Task(
        description=task_description,
        agent=agent,
        expected_output="""A detailed skincare regimen with:
        - Morning routine with specific products and order
        - Night routine with specific products and order
        - Explanation of why each product was chosen
        - How the regimen addresses the user's specific needs and environmental factors"""
    )

def generate_recommendations(user_profile: UserProfile, user_id: str) -> Dict[str, Any]:
    """Generate skincare recommendations using CrewAI."""
    try:
        # Create agent
        agent = create_skincare_agent()
        
        # Create task
        task = create_recommendation_task(agent, user_profile, user_id)
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False  # Set to False to hide internal actions from output
        )
        
        # Execute crew
        logger.info("Starting CrewAI workflow...")
        result = crew.kickoff()
        
        # Extract clean output - filter out agent action details
        result_str = str(result)
        
        # Remove verbose action logs if present
        # Look for patterns like "Action: ..." or "Action Input: ..." and remove them
        import re
        # Remove lines that start with "Action:" or "Action Input:"
        cleaned_result = re.sub(r'Action:.*?\n', '', result_str, flags=re.MULTILINE)
        cleaned_result = re.sub(r'Action Input:.*?\n', '', cleaned_result, flags=re.MULTILINE)
        cleaned_result = re.sub(r'Observation:.*?\n', '', cleaned_result, flags=re.MULTILINE)
        
        # Also remove any lines about updating history (background task)
        cleaned_result = re.sub(r'.*update.*history.*\n', '', cleaned_result, flags=re.IGNORECASE | re.MULTILINE)
        cleaned_result = re.sub(r'.*history.*updated.*\n', '', cleaned_result, flags=re.IGNORECASE | re.MULTILINE)
        
        # Parse result
        recommendations = {
            "recommendations": cleaned_result.strip(),
            "user_id": user_id,
            "profile": user_profile.to_dict()
        }
        
        logger.info("CrewAI workflow completed")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return {
            "error": str(e),
            "recommendations": None
        }
