"""User profile data models and validation."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum

class SkinType(str, Enum):
    """Skin type enumeration."""
    DRY = "dry"
    OILY = "oily"
    COMBINATION = "combination"
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    MATURE = "mature"

class ScreenTime(str, Enum):
    """Screen time categories."""
    LOW = "low"  # < 4 hours
    MEDIUM = "medium"  # 4-8 hours
    HIGH = "high"  # > 8 hours

class SunExposure(str, Enum):
    """Sun exposure categories."""
    LOW = "low"  # Mostly indoors, minimal sun
    MEDIUM = "medium"  # Some outdoor time, occasional sun
    HIGH = "high"  # Significant outdoor time, regular sun exposure

class UserProfile(BaseModel):
    """User profile model for skincare assessment."""
    
    # Basic Information
    skin_type: Optional[SkinType] = Field(None, description="User's skin type")
    region_origin: Optional[str] = Field(None, description="Region of origin")
    region_stay: Optional[str] = Field(None, description="Current region of stay")
    occupation: Optional[str] = Field(None, description="User's occupation")
    
    # Environmental Factors
    screen_time: Optional[ScreenTime] = Field(None, description="Daily screen time")
    sun_exposure: Optional[SunExposure] = Field(None, description="Sun exposure level")
    
    # Additional Details
    skin_concerns: List[str] = Field(default_factory=list, description="List of skin concerns")
    current_products: List[str] = Field(default_factory=list, description="Currently used products")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    budget_range: Optional[str] = Field(None, description="Budget preference")
    preferred_brands: List[str] = Field(default_factory=list, description="Preferred brands")
    
    # Metadata
    user_id: Optional[str] = Field(None, description="Unique user identifier")
    profile_complete: bool = Field(False, description="Whether profile is complete")
    
    @validator('skin_concerns', 'current_products', 'allergies', 'preferred_brands', pre=True)
    def convert_to_list(cls, v):
        """Convert string to list if needed."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v or []
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields."""
        required_fields = [
            'skin_type', 'region_origin', 'region_stay', 
            'occupation', 'screen_time', 'sun_exposure'
        ]
        missing = []
        for field in required_fields:
            if getattr(self, field) is None:
                missing.append(field)
        return missing
    
    def is_complete(self) -> bool:
        """Check if profile has all required fields."""
        return len(self.get_missing_fields()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "skin_type": self.skin_type.value if self.skin_type else None,
            "region_origin": self.region_origin,
            "region_stay": self.region_stay,
            "occupation": self.occupation,
            "screen_time": self.screen_time.value if self.screen_time else None,
            "sun_exposure": self.sun_exposure.value if self.sun_exposure else None,
            "skin_concerns": self.skin_concerns,
            "current_products": self.current_products,
            "allergies": self.allergies,
            "budget_range": self.budget_range,
            "preferred_brands": self.preferred_brands,
            "user_id": self.user_id,
            "profile_complete": self.is_complete()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from dictionary."""
        return cls(**data)
