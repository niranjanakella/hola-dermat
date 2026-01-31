"""Configuration management for Hola-Dermat application."""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    
    # Embedding Model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Qdrant Collections
    PRODUCTS_COLLECTION: str = "products"
    HISTORY_COLLECTION: str = "history"
    
    # LLM Configuration
    LLM_MODEL: str = "claude-sonnet-4-5"  # Claude Sonnet 4.5
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required settings are present."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")
        if not cls.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY is required")
        return True

settings = Settings()
