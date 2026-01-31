"""Main Streamlit application for Hola-Dermat skincare assistant."""
import streamlit as st
import logging
from utils.chat_manager import ChatManager
from utils.user_profile import UserProfile, SkinType, ScreenTime, SunExposure
from agents.skincare_crew import generate_recommendations
from database.collections import initialize_collections
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Hola-Dermat - Personalized Skincare Assistant",
    page_icon="✨",
    layout="wide"
)

# Initialize session state
ChatManager.initialize_session_state()

# Initialize Qdrant collections
try:
    initialize_collections()
except Exception as e:
    logger.warning(f"Collections may already exist: {e}")

def parse_user_input(user_input: str, profile: UserProfile) -> tuple:
    """
    Parse user input and update profile accordingly.
    Returns (profile_updated, response_message)
    """
    stage = ChatManager.get_conversation_stage()
    user_input_lower = user_input.lower().strip()
    
    # Greeting stage - collect skin type
    if stage == 'greeting' or not profile.skin_type:
        # Try to extract skin type
        skin_types = {
            'dry': SkinType.DRY,
            'oily': SkinType.OILY,
            'combination': SkinType.COMBINATION,
            'normal': SkinType.NORMAL,
            'sensitive': SkinType.SENSITIVE,
            'mature': SkinType.MATURE
        }
        
        for key, value in skin_types.items():
            if key in user_input_lower:
                profile.skin_type = value
                ChatManager.set_conversation_stage('region_origin')
                return True, f"Great! I've noted your skin type as {key}. Where are you originally from? (e.g., city, country)"
        
        return False, "I'd like to understand your skin type. Could you tell me if your skin is dry, oily, combination, normal, sensitive, or mature?"
    
    # Collect region of origin
    elif stage == 'region_origin' or not profile.region_origin:
        if user_input and len(user_input.strip()) > 2:
            profile.region_origin = user_input.strip()
            ChatManager.set_conversation_stage('region_stay')
            return True, f"Thanks! I've noted your origin as {profile.region_origin}. Where are you currently living? (city, country)"
        return False, "Please tell me where you're originally from (e.g., 'New York, USA' or 'Tokyo, Japan')."
    
    # Collect region of stay
    elif stage == 'region_stay' or not profile.region_stay:
        if user_input and len(user_input.strip()) > 2:
            profile.region_stay = user_input.strip()
            ChatManager.set_conversation_stage('occupation')
            return True, f"Perfect! I've noted you're currently in {profile.region_stay}. What's your occupation? (This helps me understand your daily environment)"
        return False, "Please tell me where you're currently living."
    
    # Collect occupation
    elif stage == 'occupation' or not profile.occupation:
        if user_input and len(user_input.strip()) > 2:
            profile.occupation = user_input.strip()
            ChatManager.set_conversation_stage('screen_time')
            return True, f"Got it! I've noted your occupation as {profile.occupation}. How much time do you spend in front of screens daily? (low/medium/high or hours)"
        return False, "Please tell me about your occupation."
    
    # Collect screen time
    elif stage == 'screen_time' or not profile.screen_time:
        if 'low' in user_input_lower or '<' in user_input_lower or 'less' in user_input_lower:
            profile.screen_time = ScreenTime.LOW
        elif 'high' in user_input_lower or '>' in user_input_lower or 'more' in user_input_lower or '8' in user_input_lower:
            profile.screen_time = ScreenTime.HIGH
        else:
            profile.screen_time = ScreenTime.MEDIUM
        
        ChatManager.set_conversation_stage('sun_exposure')
        return True, f"I've noted your screen time as {profile.screen_time.value}. How much direct sunlight exposure do you get daily? (low/medium/high)"
    
    # Collect sun exposure
    elif stage == 'sun_exposure' or not profile.sun_exposure:
        if 'low' in user_input_lower or 'indoor' in user_input_lower or 'minimal' in user_input_lower:
            profile.sun_exposure = SunExposure.LOW
        elif 'high' in user_input_lower or 'outdoor' in user_input_lower or 'regular' in user_input_lower:
            profile.sun_exposure = SunExposure.HIGH
        else:
            profile.sun_exposure = SunExposure.MEDIUM
        
        ChatManager.set_conversation_stage('additional_info')
        return True, "Excellent! I have the essential information. Do you have any specific skin concerns? (e.g., acne, dark spots, wrinkles, dryness) Or type 'skip' to proceed."
    
    # Collect additional info
    elif stage == 'additional_info':
        if 'skip' in user_input_lower or 'no' in user_input_lower or 'none' in user_input_lower:
            ChatManager.mark_profile_collected()
            return True, "Perfect! I have all the information I need. Let me analyze your profile and create a personalized skincare regimen for you. This may take a moment..."
        elif user_input:
            # Add to skin concerns
            concerns = [c.strip() for c in user_input.split(',')]
            profile.skin_concerns.extend(concerns)
            profile.skin_concerns = list(set(profile.skin_concerns))  # Remove duplicates
            
            # Ask about current products
            ChatManager.set_conversation_stage('current_products')
            return True, f"I've noted your concerns: {', '.join(profile.skin_concerns)}. Are you currently using any skincare products? (List them or type 'none')"
    
    # Collect current products
    elif stage == 'current_products':
        if 'none' not in user_input_lower and 'no' not in user_input_lower:
            products = [p.strip() for p in user_input.split(',')]
            profile.current_products.extend(products)
            profile.current_products = list(set(profile.current_products))
        
        ChatManager.mark_profile_collected()
        return True, "Perfect! I have all the information I need. Let me analyze your profile and create a personalized skincare regimen for you. This may take a moment..."
    
    # Profile complete - ready for recommendations or feedback
    else:
        return False, "I'm ready to help! If you'd like new recommendations, please refresh the page and start over."

def main():
    """Main application function."""
    
    # Header
    st.title("✨ Hola-Dermat")
    st.markdown("### Your Personalized Skincare Assistant")
    st.markdown("---")
    
    # Sidebar for profile summary
    with st.sidebar:
        st.header("Your Profile")
        profile = ChatManager.get_user_profile()
        
        if profile.skin_type:
            st.write(f"**Skin Type:** {profile.skin_type.value}")
        if profile.region_stay:
            st.write(f"**Location:** {profile.region_stay}")
        if profile.occupation:
            st.write(f"**Occupation:** {profile.occupation}")
        
        missing_fields = profile.get_missing_fields()
        if missing_fields:
            st.info(f"Still need: {', '.join(missing_fields)}")
        else:
            st.success("Profile Complete ✓")
        
        st.markdown("---")
        st.markdown("### Quick Actions")
        if st.button("Reset Conversation"):
            ChatManager.initialize_session_state()
            st.rerun()
    
    # Main chat interface
    st.header("Chat with Hola-Dermat")
    
    # Display chat history
    for message in ChatManager.get_messages():
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Show greeting if no messages
    if not ChatManager.get_messages():
        greeting = ChatManager.get_greeting_message()
        ChatManager.add_message("assistant", greeting)
        with st.chat_message("assistant"):
            st.write(greeting)
    
    # User input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message
        ChatManager.add_message("user", user_input)
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process input
        profile = ChatManager.get_user_profile()
        
        # First, try intelligent extraction from the message
        extracted_any, _ = ChatManager.extract_profile_info(user_input, profile)
        
        # Update profile fields in session state
        ChatManager.update_profile_field('skin_type', profile.skin_type)
        ChatManager.update_profile_field('region_origin', profile.region_origin)
        ChatManager.update_profile_field('region_stay', profile.region_stay)
        ChatManager.update_profile_field('occupation', profile.occupation)
        ChatManager.update_profile_field('screen_time', profile.screen_time)
        ChatManager.update_profile_field('sun_exposure', profile.sun_exposure)
        ChatManager.update_profile_field('skin_concerns', profile.skin_concerns)
        ChatManager.update_profile_field('current_products', profile.current_products)
        
        # Check if profile is complete after extraction
        if profile.is_complete():
            ChatManager.mark_profile_collected()
            response = "Perfect! I have all the information I need. Let me analyze your profile and create a personalized skincare regimen for you. This may take a moment..."
        else:
            # Use the traditional parsing for remaining fields
            profile_updated, response = parse_user_input(user_input, profile)
        
        # Add assistant response
        ChatManager.add_message("assistant", response)
        with st.chat_message("assistant"):
            st.write(response)
        
        # If profile is complete, trigger CrewAI workflow
        if ChatManager.is_profile_collected() and not ChatManager.get_recommendations():
            with st.spinner("Analyzing your profile and generating personalized recommendations..."):
                try:
                    user_id = ChatManager.get_user_id()
                    recommendations = generate_recommendations(profile, user_id)
                    
                    if recommendations.get('error'):
                        error_msg = f"I encountered an error: {recommendations['error']}. Please try again."
                        ChatManager.add_message("assistant", error_msg)
                        st.error(error_msg)
                    else:
                        rec_text = recommendations.get('recommendations', 'No recommendations generated.')
                        ChatManager.set_recommendations(recommendations)
                        ChatManager.add_message("assistant", rec_text)
                        
                        with st.chat_message("assistant"):
                            st.markdown("### Your Personalized Skincare Regimen")
                            st.markdown(rec_text)
                            
                            st.markdown("---")
                            st.markdown("### Feedback")
                            st.markdown("How would you like to proceed?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("👍 These recommendations look good"):
                                    feedback_msg = "Thank you for your feedback! I've saved your preferences."
                                    ChatManager.add_message("user", "👍 These recommendations look good")
                                    ChatManager.add_message("assistant", feedback_msg)
                                    st.success(feedback_msg)
                            
                            with col2:
                                if st.button("🔄 Request different products"):
                                    feedback_msg = "I'll help you find alternatives. What would you like to change?"
                                    ChatManager.add_message("user", "🔄 Request different products")
                                    ChatManager.add_message("assistant", feedback_msg)
                                    st.info(feedback_msg)
                
                except Exception as e:
                    logger.error(f"Error generating recommendations: {e}")
                    error_msg = f"I encountered an error while generating recommendations: {str(e)}. Please check your API keys and try again."
                    ChatManager.add_message("assistant", error_msg)
                    st.error(error_msg)
        
        # Rerun to update UI
        st.rerun()

if __name__ == "__main__":
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.info("Please create a `.env` file with your API keys. See `.env.example` for reference.")
        st.stop()
    
    main()
