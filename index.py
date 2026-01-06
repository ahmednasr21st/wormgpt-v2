import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import time
from datetime import datetime
import io

# ==========================================
# 1. SYSTEM CONFIGURATION & CONSTANTS
# ==========================================
st.set_page_config(
    page_title="WORM-GPT: ULTIMATE",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
FILES_DIR = "worm_data"
CHATS_FILE = os.path.join(FILES_DIR, "history.json")
CONFIG_FILE = os.path.join(FILES_DIR, "config.json")

# Ensure directory exists
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# ==========================================
# 2. ADVANCED CSS (Gemini-Like Dark Theme)
# ==========================================
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Chat Bubbles - Gemini Style */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* User Message */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #21262d !important;
        border-radius: 20px;
        margin-bottom: 15px;
        border: 1px solid #30363d;
    }
    
    /* AI Message */
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: transparent !important;
        padding-left: 0 !important;
    }
    
    /* Input Area - Fixed Bottom */
    div[data-testid="stChatInputContainer"] {
        background-color: #0e1117;
        border-top: 1px solid #30363d;
        padding-bottom: 20px;
        padding-top: 20px;
    }
    
    div[data-testid="stChatInput"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 25px;
    }
    
    /* Buttons & Interactive Elements */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Code Blocks */
    code {
        color: #ff7b72 !important;
        font-family: 'Fira Code', monospace;
    }
    
    /* Header Animation */
    @keyframes pulse {
        0% { opacity: 0.5; }
        50% { opacity: 1; }
        100% { opacity: 0.5; }
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #2ea043;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE CLASSES (Object Oriented Design)
# ==========================================

class DataManager:
    """Handles all file I/O operations (Persistence Layer)"""
    
    @staticmethod
    def load_json(filepath, default_content):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return default_content
        return default_content

    @staticmethod
    def save_json(filepath, data):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            st.error(f"Data Save Error: {e}")

class GeminiBrain:
    """Handles logic for Google Gemini API interaction"""
    
    def __init__(self, api_key, model_name="gemini-1.5-flash", system_prompt="", temp=0.7):
        self.api_key = api_key
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.temperature = temp
        self.setup()

    def setup(self):
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature
                )
            )
        else:
            self.model = None

    def generate_stream(self, history, image=None):
        """
        Generates a streaming response. 
        Supports Multimodal (Text + Image).
        """
        if not self.model:
            yield "⚠️ API Key Missing! Please verify settings."
            return

        # Prepare Content
        user_msg = history[-1]["parts"][0]
        
        # If image exists, we use generate_content instead of chat session for this turn
        if image:
            try:
                # Combining text prompt + image
                response = self.model.generate_content([user_msg, image], stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"❌ Vision Error: {str(e)}"
        else:
            # Text-only chat session
            # Convert history format for Gemini
            gemini_hist = []
            for msg in history[:-1]: # Exclude last message
                gemini_hist.append({
                    "role": "user" if msg["role"] == "user" else "model", 
                    "parts": msg["parts"]
                })
            
            try:
                chat = self.model.start_chat(history=gemini_hist)
                response = chat.send_message(user_msg, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"❌ Text Error: {str(e)}"

# ==========================================
# 4. APP LOGIC & SESSION STATE
# ==========================================

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = DataManager.load_json(CHATS_FILE, {})
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# --- Sidebar Logic ---
with st.sidebar:
    st.markdown("## 🧬 CONTROL PANEL")
    
    # API Configuration
    api_key_input = st.text_input("Gemini API Key", type="password", help="Get free key from Google AI Studio")
    if api_key_input:
        st.session_state.api_key = api_key_input
    else:
        # Check secrets
        st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", None)

    st.markdown("---")
    
    # Model Settings (Mimicking Advanced Controls)
    with st.expander("⚙️ Neural Settings", expanded=False):
        sys_prompt = st.text_area("System Persona", value="You are a helpful, expert AI assistant. You answer comprehensively.", height=100)
        temp_slider = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.7)
        model_select = st.selectbox("Model Core", ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro"])
    
    st.markdown("---")
    
    # Chat Management
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.current_chat_id = None
        st.session_state.uploaded_image = None
        st.rerun()

    st.markdown("### 🗂️ History")
    
    # Display Chats
    chat_ids = list(st.session_state.history.keys())
    chat_ids.reverse() # Newest first
    
    for chat_id in chat_ids:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(f"💬 {chat_id[:15]}...", key=f"load_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.history[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = None
                DataManager.save_json(CHATS_FILE, st.session_state.history)
                st.rerun()

# ==========================================
# 5. MAIN INTERFACE
# ==========================================

# Header
st.markdown(f"""
    <h1><span class="status-indicator"></span>WORM-GPT <span style="font-size:0.5em; color:#888;">GEN-Z ARCHITECTURE</span></h1>
""", unsafe_allow_html=True)

# Initialize Brain
brain = GeminiBrain(
    api_key=st.session_state.api_key, 
    model_name=model_select,
    system_prompt=sys_prompt,
    temp=temp_slider
)

# Chat Logic
if not st.session_state.current_chat_id:
    st.info("👋 Ready to process. Start a new chat or select from history.")
    # Show Image Uploader when no chat is active or at start of new chat
    img_file = st.file_uploader("👁️ Upload Image for Analysis (Multimodal)", type=['png', 'jpg', 'jpeg'])
    if img_file:
        st.image(img_file, caption="Vision Input Loaded", width=300)
        st.session_state.uploaded_image = Image.open(img_file)
else:
    # Load and display history
    chat_data = st.session_state.history.get(st.session_state.current_chat_id, [])
    
    for msg in chat_data:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["parts"][0]) # Text content
            # Could add logic here to display stored images if we saved them as base64

# --- Input Handling ---
prompt = st.chat_input("Enter your directive...")

if prompt:
    # 1. Create ID if new
    if not st.session_state.current_chat_id:
        new_id = f"Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.current_chat_id = new_id
        st.session_state.history[new_id] = []

    # 2. Add User Message to State
    # Note: 'parts' is a list to mimic Gemini API structure
    st.session_state.history[st.session_state.current_chat_id].append({
        "role": "user",
        "parts": [prompt]
    })
    
    # 3. Display User Message Immediately
    with st.chat_message("user"):
        st.markdown(prompt)
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, width=200, caption="Attached Image")

    # 4. Generate AI Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Get history for the model
        current_history = st.session_state.history[st.session_state.current_chat_id]
        
        # Stream response
        stream_gen = brain.generate_stream(
            history=current_history, 
            image=st.session_state.uploaded_image
        )
        
        for chunk in stream_gen:
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")
            time.sleep(0.01) # Simulate typing effect
        
        response_placeholder.markdown(full_response)
        
        # 5. Save AI Message
        st.session_state.history[st.session_state.current_chat_id].append({
            "role": "model",
            "parts": [full_response]
        })
        
        # Clear image after one use (like Gemini usually does per turn)
        if st.session_state.uploaded_image:
             st.session_state.uploaded_image = None
             
        # Save to Disk
        DataManager.save_json(CHATS_FILE, st.session_state.history)

        # Force rerun to update UI state properly (optional but safer)
        # st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>WORM-GPT v4.0 • Powered by Gemini Flash • Unrestricted Architecture</div>", unsafe_allow_html=True)
