import streamlit as st
import google.generativeai as genai
import os
import time
import uuid # For unique keys to force reruns if needed

# --- 0. Set Page Config ---
st.set_page_config(layout="wide", page_title="ChatGPT Clone", initial_sidebar_state="expanded")

# --- 1. CSS Injection (Strict Adherence Required) ---
st.markdown(
    """
    <style>
    /* Global App Styling */
    .stApp {
        background-color: #343541;
        color: #ECECF1;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
    }

    /* Remove Streamlit default header/footer whitespace */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 10rem; /* Space for fixed input + disclaimer */
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 768px; /* Centralize chat like ChatGPT */
        margin-left: auto;
        margin-right: auto;
        min-height: 100vh; /* Ensure chat window is at least full height */
    }

    /* Target Streamlit's default padding at the very top/bottom of the app */
    .st-emotion-cache-z5fcl4 { /* This class is often on the main content block */
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    .st-emotion-cache-uf99v8 { /* This class can also affect main content spacing */
        padding-top: 0rem;
        padding-bottom: 0rem;
    }


    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #202123;
        color: #ECECF1;
        padding-top: 0rem;
        padding-left: 0rem;
        padding-right: 0rem;
    }

    /* Adjust padding within sidebar content block */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* New Chat Button */
    .new-chat-button .stButton > button {
        width: 100%;
        background-color: transparent;
        color: #ECECF1;
        border: 1px solid #565869;
        border-radius: 4px;
        padding: 10px 15px;
        font-size: 16px;
        transition: background-color 0.2s;
        margin-bottom: 1rem; /* Space below new chat button */
        display: flex; /* Align content inside button */
        align-items: center;
        justify-content: center;
        gap: 8px; /* Space between icon and text */
    }
    .new-chat-button .stButton > button:hover {
        background-color: #2A2B32;
        border-color: #565869;
    }
    .new-chat-button .stButton > button svg { /* Style for icon inside button */
        fill: #ECECF1;
        width: 18px;
        height: 18px;
    }

    /* Sidebar Chat History Item */
    .sidebar-chat-history-item {
        padding: 10px;
        margin-bottom: 5px;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.2s;
        font-size: 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #ECECF1; /* Ensure text color */
    }
    .sidebar-chat-history-item:hover {
        background-color: #2A2B32;
    }

    /* Sidebar Divider for History */
    .sidebar-divider {
        border-top: 1px solid #565869;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* User Profile at bottom of sidebar */
    .sidebar-profile-container {
        position: sticky; /* Make it sticky */
        bottom: 0;
        width: 100%; /* Occupy full width of its parent (sidebar) */
        padding: 1rem;
        border-top: 1px solid #565869;
        background-color: #202123; /* Ensure it covers content behind */
        display: flex;
        align-items: center;
        gap: 10px;
        box-sizing: border-box; /* Include padding in width */
    }
    .sidebar-profile-avatar {
        border-radius: 2px;
        width: 24px;
        height: 24px;
        background-color: #ECECF1; /* Simple background for avatar icon */
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .sidebar-profile-avatar svg {
        fill: #343541; /* User icon color */
        width: 18px;
        height: 18px;
    }
    .sidebar-profile-text {
        color: #ECECF1;
        font-size: 14px;
    }


    /* Main Chat Window Styling */
    /* stChatMessage specific styling, overriding Streamlit's default message bubble appearance */
    [data-testid="stChatMessage"] {
        padding: 1.5rem 1.5rem; /* Adjust padding as per ChatGPT */
        margin-bottom: 0rem; /* No margin-bottom, managed by parent container */
        border-radius: 0; /* Remove default border-radius */
        display: flex; /* Flexbox for avatar and content */
        align-items: flex-start; /* Align content to top */
        gap: 1rem; /* Space between avatar and message */
        min-width: 100%; /* Ensure full width usage */
        box-sizing: border-box; /* Include padding in width */
        border-bottom: 1px solid #3c3d4f; /* Subtle separator */
    }
    [data-testid="stChatMessage"]:first-child {
        border-top: 1px solid #3c3d4f; /* Top border for the very first message */
    }

    /* User Message Bubble */
    [data-testid="stChatMessage"][data-chatter="user"] {
        background-color: transparent; /* User message transparent */
    }
    /* AI Message Bubble */
    [data-testid="stChatMessage"][data-chatter="assistant"] {
        background-color: #444654; /* AI message background */
    }

    /* Avatars */
    [data-testid="stChatMessage"] .st-bh { /* Target the avatar container */
        width: 30px; /* Fixed avatar size */
        height: 30px;
        flex-shrink: 0; /* Prevent avatar from shrinking */
        display: flex;
        justify-content: center;
        align-items: center;
        border-radius: 2px; /* Square with rounded corners */
        overflow: hidden; /* Important for avatar svg/img to not bleed */
    }

    /* User Avatar */
    [data-testid="stChatMessage"][data-chatter="user"] .st-bh {
        background-color: transparent; /* No background for user avatar */
    }
    [data-testid="stChatMessage"][data-chatter="user"] .st-bh svg { /* If using icon */
        fill: #ECECF1; /* User icon color */
        width: 20px;
        height: 20px;
    }

    /* AI Avatar */
    [data-testid="stChatMessage"][data-chatter="assistant"] .st-bh {
        background-color: #19C37D; /* Green background for AI avatar */
    }
    [data-testid="stChatMessage"][data-chatter="assistant"] .st-bh svg {
        fill: white; /* White SVG logo for AI */
        width: 20px;
        height: 20px;
    }

    [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        flex-grow: 1; /* Allow markdown content to take available space */
        color: #ECECF1; /* Ensure text color is consistent */
        line-height: 1.6; /* Improve readability */
        word-wrap: break-word; /* Ensure long words break */
        overflow-wrap: break-word; /* For better browser support */
    }
    [data-testid="stChatMessage"] p {
        margin-bottom: 0.5rem;
    }
    [data-testid="stChatMessage"] p:last-child {
        margin-bottom: 0;
    }

    /* Markdown Specifics - Code Blocks, Tables, Bold */
    [data-testid="stChatMessage"] pre { /* Code blocks */
        background-color: #000;
        color: #f8f8f2;
        padding: 1em;
        border-radius: 5px;
        overflow-x: auto;
        font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
        line-height: 1.4;
        font-size: 0.9em;
    }
    [data-testid="stChatMessage"] code { /* Inline code */
        background-color: #2A2B32;
        color: #f8f8f2;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-size: 85%;
        font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace;
    }
    [data-testid="stChatMessage"] table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    [data-testid="stChatMessage"] th, [data-testid="stChatMessage"] td {
        border: 1px solid #565869;
        padding: 8px;
        text-align: left;
    }
    [data-testid="stChatMessage"] th {
        background-color: #2A2B32;
    }
    [data-testid="stChatMessage"] strong {
        font-weight: bold;
    }


    /* Empty State / Welcome Screen */
    .empty-state {
        text-align: center;
        color: #ECECF1;
        margin-top: 10vh; /* Adjust as needed */
        margin-bottom: 2rem;
    }
    .empty-state h1 {
        font-size: 2.5em;
        margin-bottom: 1em;
        color: #ECECF1;
    }
    .empty-state-card {
        background-color: #40414F;
        border: 1px solid #565869;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        height: 100%; /* Ensure equal height in a grid */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .empty-state-card h3 {
        color: #ECECF1;
        font-size: 1.1em;
        margin-top: 0;
        margin-bottom: 10px;
    }
    .empty-state-card ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .empty-state-card li {
        margin-bottom: 8px;
        font-size: 0.9em;
        color: #9A9B9F; /* Slightly dimmer for list items */
    }
    .empty-state-card .stButton > button {
        background-color: #40414F;
        border: 1px solid #565869;
        color: #ECECF1;
        border-radius: 8px;
        padding: 8px 15px;
        font-size: 0.9em;
        transition: background-color 0.2s;
        width: auto;
        line-height: 1.2;
        min-height: 38px; /* Ensure consistent button height */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .empty-state-card .stButton > button:hover {
        background-color: #2A2B32;
        border-color: #565869;
    }
    .empty-state-card .stButton {
        margin-top: 5px;
    }
    .empty-state-card .stButton > button:active {
        background-color: #19C37D; /* Active primary button */
        border-color: #19C37D;
    }

    /* Input Area (Footer) */
    div[data-testid="stForm"] { /* Targets the form containing st.chat_input */
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #343541; /* Match global background */
        padding: 1rem 0; /* Vertical padding */
        box-shadow: 0 -5px 15px rgba(0,0,0,0.1);
        z-index: 100;
    }

    div[data-testid="stForm"] > div > div { /* Targets the content block inside the form */
        max-width: 768px; /* Match main chat width */
        margin-left: auto;
        margin-right: auto;
        padding: 0 1rem; /* Horizontal padding for alignment */
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    div[data-testid="stForm"] > div > div > div:nth-child(1) { /* Targets the chat_input widget */
        width: 100%;
        position: relative;
    }

    [data-testid="stChatInput"] > div > div > textarea {
        background-color: #40414F;
        color: #ECECF1;
        border-radius: 12px;
        border: 1px solid transparent; /* Remove default Streamlit border */
        padding: 12px 15px; /* Adjust padding */
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
        min-height: 48px; /* Ensure a decent height */
        resize: none; /* Disable manual resize */
        line-height: 1.5;
    }

    /* Placeholder color */
    [data-testid="stChatInput"] > div > div > textarea::placeholder {
        color: #8E8EA0;
        opacity: 1; /* Ensure placeholder is visible */
    }

    /* Input focus style */
    [data-testid="stChatInput"] > div > div > textarea:focus {
        border-color: #19C37D; /* Green border on focus */
        box-shadow: 0 0 0 2px rgba(25, 195, 125, 0.5);
        outline: none;
    }

    /* Send button inside chat_input */
    [data-testid="stChatInput"] button {
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        background-color: transparent;
        border: none;
        color: #8E8EA0; /* Default icon color */
        padding: 0;
        margin: 0;
        cursor: pointer;
        z-index: 1;
    }
    [data-testid="stChatInput"] button:disabled svg {
        fill: #565869; /* Grey out send button when disabled */
    }

    [data-testid="stChatInput"] button svg {
        fill: #8E8EA0; /* Send icon color */
        width: 24px;
        height: 24px;
        transition: fill 0.2s;
    }
    [data-testid="stChatInput"] button:hover svg {
        fill: #ECECF1; /* Hover color */
    }

    /* Disclaimer text */
    .disclaimer {
        font-size: 12px;
        color: #9A9B9F;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 0rem;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #565869;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #6D6F81;
    }

    /* Streamlit toast messages */
    .st-emotion-cache-1f8rfx1 { /* target for toast container */
        background-color: #40414F; /* Match input box */
        color: #ECECF1;
        border: 1px solid #565869;
        box-shadow: 0 0 15px rgba(0,0,0,0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. Google Gemini API Configuration ---
# Check for API key in environment variables or Streamlit secrets
if "GEMINI_API_KEY" not in os.environ:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("GEMINI_API_KEY not found. Please set it as an environment variable or in `secrets.toml`.")
        st.stop()

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Failed to initialize Gemini model: {e}. Check your API key and network connection.")
    st.stop() # Stop the app if model can't be initialized

# --- 3. Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state: # For Gemini's specific history format
    st.session_state.chat_history = []
if "prompt_input" not in st.session_state: # For pre-populating input from examples
    st.session_state.prompt_input = ""
if "new_chat_trigger" not in st.session_state: # To ensure rerun for new chat
    st.session_state.new_chat_trigger = uuid.uuid4()


# --- Helper Functions ---
def reset_chat():
    """Clears chat history and forces a full app rerun."""
    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.prompt_input = ""
    st.session_state.new_chat_trigger = uuid.uuid4() # Update trigger to force rerun
    st.experimental_rerun()

def to_gemini_history(messages):
    """Converts Streamlit messages format to Gemini chat history format."""
    gemini_history = []
    for message in messages:
        if message["role"] == "user":
            gemini_history.append({"role": "user", "parts": [message["content"]]})
        elif message["role"] == "assistant":
            gemini_history.append({"role": "model", "parts": [message["content"]]})
    return gemini_history

def generate_response():
    """Handles sending user prompt to Gemini and streaming the response."""
    prompt = st.session_state.prompt_input # Get current input from the text_input
    if not prompt:
        return

    # Append user message to display messages
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message immediately in the chat stream
    user_avatar_html = """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
        </svg>
    """
    with st.chat_message("user", avatar=user_avatar_html):
        st.markdown(prompt)

    # Prepare chat history for Gemini (excluding the current user message, which is passed separately)
    # The `messages` state might contain the current user message already from the previous line.
    # We need to ensure chat_history passed to Gemini includes ALL *previous* turns.
    # The `chat` object in Gemini handles the current user prompt.
    gemini_history_for_context = to_gemini_history(st.session_state.messages[:-1])


    try:
        # Start a new chat session with existing history
        chat = model.start_chat(history=gemini_history_for_context)
        response_stream = chat.send_message(prompt, stream=True)

        full_response = ""
        ai_avatar_html = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
        """
        with st.chat_message("assistant", avatar=ai_avatar_html):
            message_placeholder = st.empty()
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") # Blinking cursor
                    time.sleep(0.02) # Simulate typing speed, adjust as needed
            message_placeholder.markdown(full_response) # Remove cursor at the end

        # Append AI response to display messages and Gemini chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_history.append({"role": "model", "parts": [full_response]})

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.toast("🚨 Network Error or API issue. Please try again.", icon="🚨")
    finally:
        st.session_state.prompt_input = "" # Clear the input after processing


# --- A. Sidebar (Navigation) ---
with st.sidebar:
    st.markdown('<div class="new-chat-button">', unsafe_allow_html=True)
    if st.button(
        """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-plus">
            <line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>New Chat""",
        key="new_chat_button",
        unsafe_allow_html=True
    ):
        reset_chat()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<h3>Previous 7 Days</h3>", unsafe_allow_html=True)
    # Mock Chat History (truncated for display)
    mock_history = [
        "Explain quantum computing in simple terms",
        "Give me some ideas for a date night in NYC",
        "Write a python function for a fibonacci sequence",
        "Summarize the plot of the Great Gatsby",
        "How do I fix a leaky faucet?",
        "Plan a 3-day trip to Tokyo",
        "Describe the impact of AI on job markets"
    ]
    for i, item in enumerate(mock_history):
        # Using a button for clickability for mock history
        if st.button(item, key=f"sidebar_chat_{i}", help="Click to load chat (mock)", use_container_width=True):
            st.toast(f"Loading '{item}' (mock function)", icon="💬")
        # Direct markdown for display if not clickable
        # st.markdown(f'<div class="sidebar-chat-history-item">{item}</div>', unsafe_allow_html=True)


    # User Profile (Fixed at bottom)
    # Using st.container to create a distinct div for sticky positioning
    st.markdown('<div class="sidebar-profile-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-profile-avatar">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        </div>
        <div class="sidebar-profile-text">User</div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# --- B. The Chat Stream (Main Display) ---

# Empty State Logic
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
            <img src="https://i.ibb.co/L5k6jLz/wormgpt-logo.png" width="90px" alt="WORM-GPT Logo" style="filter: invert(1); opacity: 0.7;">
            <h1>WORM-GPT v2.0</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="empty-state-card">', unsafe_allow_html=True)
        st.markdown("<h3>Examples</h3>", unsafe_allow_html=True)
        # Wrap buttons in markdown list for consistent styling if needed
        if st.button('"Explain quantum computing in simple terms"', key="ex1_btn"):
            st.session_state.prompt_input = "Explain quantum computing in simple terms"
            st.rerun() # Trigger a rerun to process the prompt and generate response
        if st.button('"Brainstorm ideas for a 10-year-old\'s birthday party"', key="ex2_btn"):
            st.session_state.prompt_input = "Brainstorm ideas for a 10-year-old's birthday party"
            st.rerun()
        if st.button('"How do I make a perfect sourdough bread?"', key="ex3_btn"):
            st.session_state.prompt_input = "How do I make a perfect sourdough bread?"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="empty-state-card">', unsafe_allow_html=True)
        st.markdown("<h3>Capabilities</h3>", unsafe_allow_html=True)
        st.markdown("""
            <ul>
                <li>Remembers what user said earlier in conversation</li>
                <li>Allows user to provide follow-up corrections</li>
                <li>Trained to decline inappropriate requests</li>
            </ul>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="empty-state-card">', unsafe_allow_html=True)
        st.markdown("<h3>Limitations</h3>", unsafe_allow_html=True)
        st.markdown("""
            <ul>
                <li>May occasionally generate incorrect information</li>
                <li>May occasionally produce harmful instructions or biased content</li>
                <li>Limited knowledge of world and events after 2023</li>
            </ul>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# Message Rendering
for message in st.session_state.messages:
    avatar_html = ""
    if message["role"] == "user":
        # User avatar SVG
        avatar_html = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        """
    elif message["role"] == "assistant":
        # AI (WORM-GPT) avatar SVG (Lightning bolt)
        avatar_html = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
        """
    with st.chat_message(message["role"], avatar=avatar_html):
        st.markdown(message["content"])

# --- C. The Input Area (The "Footer") ---

# Using a form to capture enter key press for st.chat_input
with st.form(key="chat_input_form", clear_on_submit=False):
    # The actual chat input widget
    st.chat_input("Message WORM-GPT...", key="prompt_input", on_submit=generate_response)
    # Disclaimer text below the input box
    st.markdown('<p class="disclaimer">WORM-GPT can make mistakes. Consider checking important information.</p>', unsafe_allow_html=True)
    # A dummy submit button is needed for the form to correctly trigger on_submit for the chat_input
    # It will be hidden by the CSS
    st.form_submit_button("Submit", style="display: none;")

# If a prompt was set by an example button and it's a new chat, immediately generate a response
# This check prevents re-triggering on every rerun after a message is sent.
if st.session_state.prompt_input and not st.session_state.messages:
    generate_response()
    st.rerun() # Rerun to display the new message and clear the input properly
