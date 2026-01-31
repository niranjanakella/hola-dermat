"""Streamlit chat state management and conversation flow."""
import streamlit as st
from typing import List, Dict, Any, Optional
from utils.user_profile import UserProfile, SkinType, ScreenTime, SunExposure
import uuid
import re

class ChatManager:
    """Manages chat state and conversation flow."""
    
    @staticmethod
    def initialize_session_state():
        """Initialize Streamlit session state variables."""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = UserProfile()
        
        if 'user_id' not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())
            st.session_state.user_profile.user_id = st.session_state.user_id
        
        if 'conversation_stage' not in st.session_state:
            st.session_state.conversation_stage = 'greeting'
        
        if 'profile_collected' not in st.session_state:
            st.session_state.profile_collected = False
        
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = None
    
    @staticmethod
    def add_message(role: str, content: str):
        """Add a message to chat history."""
        st.session_state.messages.append({"role": role, "content": content})
    
    @staticmethod
    def get_messages() -> List[Dict[str, str]]:
        """Get all chat messages."""
        return st.session_state.messages
    
    @staticmethod
    def get_user_profile() -> UserProfile:
        """Get current user profile."""
        return st.session_state.user_profile
    
    @staticmethod
    def update_profile_field(field: str, value: Any):
        """Update a profile field."""
        if hasattr(st.session_state.user_profile, field):
            setattr(st.session_state.user_profile, field, value)
    
    @staticmethod
    def get_user_id() -> str:
        """Get user ID."""
        return st.session_state.user_id
    
    @staticmethod
    def set_conversation_stage(stage: str):
        """Set conversation stage."""
        st.session_state.conversation_stage = stage
    
    @staticmethod
    def get_conversation_stage() -> str:
        """Get current conversation stage."""
        return st.session_state.conversation_stage
    
    @staticmethod
    def mark_profile_collected():
        """Mark profile as collected."""
        st.session_state.profile_collected = True
        st.session_state.conversation_stage = 'ready_for_recommendations'
    
    @staticmethod
    def is_profile_collected() -> bool:
        """Check if profile is collected."""
        return st.session_state.profile_collected
    
    @staticmethod
    def set_recommendations(recommendations: Dict[str, Any]):
        """Store recommendations."""
        st.session_state.recommendations = recommendations
    
    @staticmethod
    def get_recommendations() -> Optional[Dict[str, Any]]:
        """Get stored recommendations."""
        return st.session_state.recommendations
    
    @staticmethod
    def get_greeting_message() -> str:
        """Get initial greeting message."""
        return """Hello! 👋 I'm Hola-Dermat, your personalized skincare assistant. 

I'm here to help you create a customized morning and night skincare regimen tailored to your unique needs. 

Please tell me about yourself - your skin type, where you're from, where you currently live, your occupation, screen time, sun exposure, and any current products you're using. You can share all this information at once!"""
    
    @staticmethod
    def extract_profile_info(user_input: str, profile: UserProfile) -> tuple[bool, str]:
        """
        Intelligently extract all profile information from user input.
        Returns (all_info_extracted, response_message)
        """
        user_input_lower = user_input.lower()
        extracted_any = False
        
        # Extract skin type
        skin_type_patterns = {
            'dry': SkinType.DRY,
            'oily': SkinType.OILY,
            'combination': SkinType.COMBINATION,
            'normal': SkinType.NORMAL,
            'sensitive': SkinType.SENSITIVE,
            'mature': SkinType.MATURE
        }
        
        for key, value in skin_type_patterns.items():
            if key in user_input_lower and not profile.skin_type:
                profile.skin_type = value
                extracted_any = True
                break
        
        # Extract region of origin (look for patterns like "from", "originally from", "born in")
        origin_patterns = [
            r'(?:from|originally from|born in|grew up in)\s+([^,\.]+?)(?:,|\.|$)',
            r'(?:i am|i\'m)\s+from\s+([^,\.]+?)(?:,|\.|$)',
        ]
        if not profile.region_origin:
            for pattern in origin_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    profile.region_origin = match.group(1).strip()
                    extracted_any = True
                    break
        
        # Extract current region (look for patterns like "stay in", "live in", "currently in", "staying in")
        stay_patterns = [
            r'(?:stay|staying|live|living|currently in|currently at)\s+(?:in|at)?\s*([^,\.]+?)(?:,|\.|$)',
            r'(?:i stay|i\'m staying|i live|i\'m living)\s+(?:in|at)?\s*([^,\.]+?)(?:,|\.|$)',
        ]
        if not profile.region_stay:
            for pattern in stay_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    region = match.group(1).strip()
                    # Clean up common words
                    region = re.sub(r'\s+(in|at|the)$', '', region, flags=re.IGNORECASE)
                    profile.region_stay = region
                    extracted_any = True
                    break
        
        # Extract occupation (look for common patterns)
        if not profile.occupation:
            # Common occupation keywords
            occupation_keywords = ['engineer', 'developer', 'doctor', 'teacher', 'student', 'designer', 'manager', 
                                  'analyst', 'consultant', 'writer', 'artist', 'scientist', 'researcher', 'professor',
                                  'lawyer', 'accountant', 'nurse', 'therapist', 'counselor', 'coach', 'trainer',
                                  'chef', 'baker', 'barista', 'waiter', 'waitress', 'server', 'cashier', 'retail',
                                  'sales', 'marketing', 'hr', 'human resources', 'it', 'information technology',
                                  'software', 'hardware', 'data', 'business', 'finance', 'banking', 'insurance',
                                  'real estate', 'construction', 'architect', 'plumber', 'electrician', 'mechanic',
                                  'driver', 'pilot', 'flight attendant', 'military', 'police', 'firefighter', 'paramedic',
                                  'dentist', 'pharmacist', 'surgeon', 'physician']
            for keyword in occupation_keywords:
                pattern = rf'(?:i am|i\'m|am|a)\s+(?:a|an)?\s*([^,\.]*?\b{keyword}\b[^,\.]*)'
                match = re.search(pattern, user_input_lower)
                if match:
                    profile.occupation = match.group(1).strip()
                    extracted_any = True
                    break
        
        # Extract screen time (look for patterns like "screen time", "hours", "h/day", etc.)
        if not profile.screen_time:
            # Look for numbers followed by hours/h
            hour_match = re.search(r'(\d+)\s*(?:hours?|h|hrs?)', user_input_lower)
            if hour_match:
                hours = int(hour_match.group(1))
                if hours < 4:
                    profile.screen_time = ScreenTime.LOW
                elif hours > 8:
                    profile.screen_time = ScreenTime.HIGH
                else:
                    profile.screen_time = ScreenTime.MEDIUM
                extracted_any = True
            elif 'low' in user_input_lower or 'minimal' in user_input_lower or 'little' in user_input_lower:
                profile.screen_time = ScreenTime.LOW
                extracted_any = True
            elif 'high' in user_input_lower or 'a lot' in user_input_lower or 'extensive' in user_input_lower:
                profile.screen_time = ScreenTime.HIGH
                extracted_any = True
        
        # Extract sun exposure
        if not profile.sun_exposure:
            if 'low' in user_input_lower or 'minimal' in user_input_lower or 'little' in user_input_lower or 'indoor' in user_input_lower or 'less' in user_input_lower:
                profile.sun_exposure = SunExposure.LOW
                extracted_any = True
            elif 'high' in user_input_lower or 'a lot' in user_input_lower or 'extensive' in user_input_lower or 'outdoor' in user_input_lower or 'regular' in user_input_lower:
                profile.sun_exposure = SunExposure.HIGH
                extracted_any = True
        
        # Extract skin concerns (acne, dark spots, wrinkles, etc.)
        concern_keywords = ['acne', 'pimples', 'breakouts', 'dark spots', 'hyperpigmentation', 'wrinkles', 'fine lines', 'dryness', 'oily', 'sensitive', 'redness', 'irritation', 'eczema', 'psoriasis', 'rosacea', 'blackheads', 'whiteheads', 'pores', 'texture', 'uneven', 'dull', 'dullness']
        for keyword in concern_keywords:
            if keyword in user_input_lower and keyword not in [c.lower() for c in profile.skin_concerns]:
                profile.skin_concerns.append(keyword)
                extracted_any = True
        
        # Extract current products (look for patterns like "using", "currently using", "face wash", "cleanser", etc.)
        product_keywords = ['face wash', 'cleanser', 'moisturizer', 'serum', 'toner', 'sunscreen', 'spf', 'cream', 'lotion', 'gel', 'oil', 'essence', 'ampoule', 'mask', 'scrub', 'exfoliant']
        for keyword in product_keywords:
            if keyword in user_input_lower:
                # Try to extract the product name
                product_match = re.search(rf'(?:using|use|have|with)\s+([^,\.]+?{keyword}[^,\.]*)', user_input_lower)
                if product_match:
                    product_name = product_match.group(1).strip()
                    if product_name not in profile.current_products:
                        profile.current_products.append(product_name)
                        extracted_any = True
        
        return extracted_any, ""  # Empty string means no response needed yet
