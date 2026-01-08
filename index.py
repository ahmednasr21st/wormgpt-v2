import streamlit as st
import google.generativeai as genai
import os
import time
import uuid
import datetime # For mock chat history dates

# --- 0. Streamlit Page Configuration ---
# Sets up the basic layout of the Streamlit page.
# "wide" layout uses the full browser width, ideal for cloning a modern chat interface.
# "page_title" sets the title displayed in the browser tab.
# "initial_sidebar_state" ensures the sidebar starts open.
st.set_page_config(layout="wide", page_title="WORM-GPT v2.0 Clone", initial_sidebar_state="expanded")

# --- 1. Extensive CSS Injection for Pixel-Perfect UI Clone (Strict Adherence Required) ---
# This block uses st.markdown with unsafe_allow_html=True to inject a custom <style> block
# into the Streamlit application. This is crucial for overriding Streamlit's default
# styling and achieving the ChatGPT dark mode look.
st.markdown(
    """
    <style>
    /* ---------------------------------------------------------------------------------- */
    /* GLOBAL APP STYLING: Overriding Streamlit's base elements for a consistent dark theme */
    /* ---------------------------------------------------------------------------------- */

    /* Target the main application container. */
    .stApp {
        background-color: #343541; /* Global Background */
        color: #ECECF1;           /* Main Text Color */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
        font-size: 16px;          /* Base font size */
        line-height: 1.6;         /* Improve readability of text */
        overflow-x: hidden;       /* Prevent horizontal scroll */
    }

    /* Target the main content block to control padding and width. */
    /* This ensures the chat area is centered and has appropriate margins. */
    .main .block-container {
        padding-top: 2rem;        /* Top padding for the main content area */
        padding-bottom: 10rem;    /* Generous bottom padding to make space for fixed input/disclaimer */
        padding-left: 1rem;       /* Left padding */
        padding-right: 1rem;      /* Right padding */
        max-width: 768px;         /* Max width to centralize the chat stream like ChatGPT */
        margin-left: auto;        /* Auto margins for horizontal centering */
        margin-right: auto;       /* Auto margins for horizontal centering */
        min-height: 100vh;        /* Ensure the main content area takes at least full viewport height */
        display: flex;            /* Use flexbox for the main content */
        flex-direction: column;   /* Arrange children vertically */
        justify-content: flex-start; /* Start content from the top */
    }

    /* Additional Streamlit internal classes that often add unwanted padding. */
    /* These specific classes are found via browser developer tools. */
    .st-emotion-cache-z5fcl4, .st-emotion-cache-uf99v8, .st-emotion-cache-1c7v0a5 {
        padding-top: 0rem;        /* Remove default top padding */
        padding-bottom: 0rem;     /* Remove default bottom padding */
        margin-top: 0rem;         /* Remove default top margin */
        margin-bottom: 0rem;      /* Remove default bottom margin */
    }
    .st-emotion-cache-1y4v8ft, .st-emotion-cache-1wb92y4 { /* Specific block container padding */
        padding: 0;
    }

    /* ---------------------------------------------------------------------------------- */
    /* SIDEBAR STYLING: Customizing the Streamlit sidebar to match the design system.    */
    /* ---------------------------------------------------------------------------------- */

    /* Target the sidebar container by its data-testid. */
    [data-testid="stSidebar"] {
        background-color: #202123; /* Sidebar Background */
        color: #ECECF1;           /* Sidebar Text Color */
        padding-top: 0rem;        /* Remove default padding */
        padding-left: 0rem;       /* Remove default padding */
        padding-right: 0rem;      /* Remove default padding */
        width: 260px !important;  /* Set a fixed width for the sidebar */
        min-width: 260px !important; /* Ensure min width */
        max-width: 260px !important; /* Ensure max width */
    }

    /* Adjust padding for the content *inside* the sidebar. */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    [data-testid="stSidebar"] > div { /* Inner div responsible for scrollable content */
        overflow-y: auto; /* Enable vertical scrolling */
        height: calc(100vh - 70px); /* Adjust height to make space for fixed profile at bottom */
    }

    /* Styling for the "New Chat" button at the top of the sidebar. */
    .new-chat-button .stButton > button {
        width: 100%;                  /* Full width within its container */
        background-color: transparent;/* Transparent background */
        color: #ECECF1;               /* Text color */
        border: 1px solid #565869;    /* Border color */
        border-radius: 4px;           /* Rounded corners */
        padding: 10px 15px;           /* Internal padding */
        font-size: 16px;              /* Font size */
        transition: background-color 0.2s, border-color 0.2s; /* Smooth transitions for hover */
        margin-bottom: 1.5rem;        /* Space below the button */
        display: flex;                /* Use flexbox for icon and text alignment */
        align-items: center;          /* Center items vertically */
        justify-content: center;      /* Center items horizontally */
        gap: 8px;                     /* Space between icon and text */
        cursor: pointer;              /* Indicate clickability */
    }
    /* Hover state for the "New Chat" button. */
    .new-chat-button .stButton > button:hover {
        background-color: #2A2B32;    /* Background color on hover */
        border-color: #565869;        /* Border color on hover (can be slightly different if desired) */
    }
    /* SVG icon inside the "New Chat" button. */
    .new-chat-button .stButton > button svg {
        fill: #ECECF1;                /* Icon color */
        width: 18px;                  /* Icon width */
        height: 18px;                 /* Icon height */
    }

    /* Sidebar Chat History Item Styling */
    .sidebar-chat-history-item {
        padding: 10px;                /* Padding around the text */
        margin-bottom: 5px;           /* Space between history items */
        border-radius: 4px;           /* Slightly rounded corners */
        cursor: pointer;              /* Pointer cursor on hover */
        transition: background-color 0.2s; /* Smooth transition */
        font-size: 14px;              /* Smaller font size */
        white-space: nowrap;          /* Prevent text from wrapping */
        overflow: hidden;             /* Hide overflowed text */
        text-overflow: ellipsis;      /* Show ellipsis for truncated text */
        color: #ECECF1;               /* Ensure text color is consistent */
        display: block;               /* Make the whole area clickable */
        background-color: transparent;/* Default transparent background */
    }
    /* Hover state for chat history items. */
    .sidebar-chat-history-item:hover {
        background-color: #2A2B32;    /* Highlight background on hover */
    }

    /* Sidebar Divider for History Sections (e.g., Today, Yesterday). */
    .sidebar-history-header {
        color: #8E8EA0;               /* Duller color for headers */
        font-size: 12px;              /* Smaller font size */
        text-transform: uppercase;    /* Uppercase for stylistic effect */
        margin-top: 1.5rem;           /* Space above the header */
        margin-bottom: 0.5rem;        /* Space below the header */
        padding-left: 10px;           /* Align with history items */
    }

    /* Styling for the user profile section fixed at the bottom of the sidebar. */
    .sidebar-profile-container {
        position: sticky;             /* Make it stick to the bottom */
        bottom: 0;                    /* Stick to the very bottom */
        left: 0;                      /* Align left within its parent */
        width: 100%;                  /* Occupy full width of its parent */
        padding: 1rem;                /* Internal padding */
        border-top: 1px solid #565869; /* Top border */
        background-color: #202123;    /* Ensure background covers content behind it */
        display: flex;                /* Use flexbox for avatar and text alignment */
        align-items: center;          /* Center items vertically */
        gap: 10px;                    /* Space between avatar and text */
        box-sizing: border-box;       /* Include padding in width calculation */
        z-index: 10;                  /* Ensure it stays on top of other sidebar content */
    }
    /* Styling for the user profile avatar. */
    .sidebar-profile-avatar {
        border-radius: 2px;           /* Slightly rounded corners */
        width: 24px;                  /* Fixed width */
        height: 24px;                 /* Fixed height */
        background-color: #ECECF1;    /* Simple background for the icon */
        display: flex;                /* Flexbox for centering icon */
        justify-content: center;      /* Center icon horizontally */
        align-items: center;          /* Center icon vertically */
        overflow: hidden;             /* Clip any overflowing content */
    }
    /* SVG icon inside the user profile avatar. */
    .sidebar-profile-avatar svg {
        fill: #343541;                /* User icon color */
        width: 18px;                  /* Icon width */
        height: 18px;                 /* Icon height */
    }
    /* Text for the user profile (e.g., "User"). */
    .sidebar-profile-text {
        color: #ECECF1;               /* Text color */
        font-size: 14px;              /* Font size */
    }

    /* ---------------------------------------------------------------------------------- */
    /* MAIN CHAT STREAM STYLING: Styling individual chat messages and avatars.          */
    /* ---------------------------------------------------------------------------------- */

    /* Target the chat message container provided by st.chat_message. */
    [data-testid="stChatMessage"] {
        padding: 1.5rem 1.5rem;       /* Adjust padding to match ChatGPT */
        margin-bottom: 0rem;          /* Remove default margin-bottom, managed by parent container */
        border-radius: 0;             /* Remove default border-radius */
        display: flex;                /* Use flexbox for avatar and message content */
        align-items: flex-start;      /* Align avatar and content to the top */
        gap: 1rem;                    /* Space between avatar and message text */
        min-width: 100%;              /* Ensure full width usage within its parent */
        box-sizing: border-box;       /* Include padding in width calculation */
        border-bottom: 1px solid #3c3d4f; /* Subtle separator between messages */
    }
    /* Add a top border for the very first message to complete the box look. */
    [data-testid="stChatMessage"]:first-child {
        border-top: 1px solid #3c3d4f;
    }

    /* User Message Bubble */
    [data-testid="stChatMessage"][data-chatter="user"] {
        background-color: transparent; /* User message background is transparent */
    }
    /* AI Message Bubble */
    [data-testid="stChatMessage"][data-chatter="assistant"] {
        background-color: #444654;    /* AI message background color */
    }

    /* Avatars container styling (applies to both user and assistant). */
    [data-testid="stChatMessage"] .st-bh { /* Target the avatar container, specific Streamlit internal class */
        width: 30px;                  /* Fixed avatar size */
        height: 30px;                 /* Fixed avatar size */
        flex-shrink: 0;               /* Prevent avatar from shrinking */
        display: flex;                /* Flexbox for centering avatar icon */
        justify-content: center;      /* Center icon horizontally */
        align-items: center;          /* Center icon vertically */
        border-radius: 2px;           /* Square with slightly rounded corners */
        overflow: hidden;             /* Clip any overflowing content */
    }

    /* User Avatar specific styling. */
    [data-testid="stChatMessage"][data-chatter="user"] .st-bh {
        background-color: transparent; /* User avatar has no background */
    }
    /* SVG icon inside the user avatar. */
    [data-testid="stChatMessage"][data-chatter="user"] .st-bh svg {
        fill: #ECECF1;                /* User icon color */
        width: 20px;                  /* Icon width */
        height: 20px;                 /* Icon height */
    }

    /* AI Avatar specific styling. */
    [data-testid="stChatMessage"][data-chatter="assistant"] .st-bh {
        background-color: #19C37D;    /* Green background for AI avatar */
    }
    /* SVG icon inside the AI avatar. */
    [data-testid="stChatMessage"][data-chatter="assistant"] .st-bh svg {
        fill: white;                  /* White SVG logo for AI */
        width: 20px;                  /* Icon width */
        height: 20px;                 /* Icon height */
    }

    /* Styling for the markdown content within chat messages. */
    [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        flex-grow: 1;                 /* Allow markdown content to take available space */
        color: #ECECF1;               /* Ensure text color is consistent */
        line-height: 1.6;             /* Improve readability */
        word-wrap: break-word;        /* Ensure long words break */
        overflow-wrap: break-word;    /* For better browser support */
        min-width: 0;                 /* Allow content to shrink if necessary */
    }
    /* Reset default paragraph margins within messages. */
    [data-testid="stChatMessage"] p {
        margin-top: 0.5rem;           /* Small top margin for paragraphs */
        margin-bottom: 0.5rem;        /* Small bottom margin for paragraphs */
    }
    [data-testid="stChatMessage"] p:first-child {
        margin-top: 0;                /* No top margin for the very first paragraph */
    }
    [data-testid="stChatMessage"] p:last-child {
        margin-bottom: 0;             /* No bottom margin for the very last paragraph */
    }

    /* ---------------------------------------------------------------------------------- */
    /* MARKDOWN SPECIFICS: Customizing appearance of markdown elements (code, tables, etc.) */
    /* ---------------------------------------------------------------------------------- */

    /* Code Blocks within markdown. */
    [data-testid="stChatMessage"] pre {
        background-color: #000;       /* Dark background for code blocks */
        color: #f8f8f2;               /* Light text color for code */
        padding: 1em;                 /* Padding inside code blocks */
        border-radius: 5px;           /* Slightly rounded corners */
        overflow-x: auto;             /* Enable horizontal scrolling for long lines */
        font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace; /* Monospaced font */
        line-height: 1.4;             /* Line height for readability */
        font-size: 0.9em;             /* Slightly smaller font size */
        margin-top: 1em;              /* Top margin for code blocks */
        margin-bottom: 1em;           /* Bottom margin for code blocks */
    }
    /* Inline Code snippets. */
    [data-testid="stChatMessage"] code {
        background-color: #2A2B32;    /* Darker background for inline code */
        color: #f8f8f2;               /* Light text color */
        padding: 0.2em 0.4em;         /* Small padding */
        border-radius: 3px;           /* Rounded corners */
        font-size: 85%;               /* Smaller font size */
        font-family: 'Fira Code', 'Cascadia Code', 'JetBrains Mono', monospace; /* Monospaced font */
    }
    /* Tables within markdown. */
    [data-testid="stChatMessage"] table {
        border-collapse: collapse;    /* Collapse table borders */
        width: 100%;                  /* Full width for tables */
        margin: 1em 0;                /* Vertical margins for tables */
        font-size: 0.9em;             /* Slightly smaller font size for table content */
    }
    /* Table headers and data cells. */
    [data-testid="stChatMessage"] th, [data-testid="stChatMessage"] td {
        border: 1px solid #565869;    /* Border color for cells */
        padding: 8px;                 /* Padding inside cells */
        text-align: left;             /* Left align text */
    }
    /* Table headers specific styling. */
    [data-testid="stChatMessage"] th {
        background-color: #2A2B32;    /* Darker background for table headers */
        font-weight: bold;            /* Bold text for headers */
    }
    /* Strong/Bold text. */
    [data-testid="stChatMessage"] strong {
        font-weight: bold;            /* Ensure bold text is actually bold */
    }
    /* Links */
    [data-testid="stChatMessage"] a {
        color: #19C37D; /* Green for links */
        text-decoration: none;
    }
    [data-testid="stChatMessage"] a:hover {
        text-decoration: underline;
    }

    /* ---------------------------------------------------------------------------------- */
    /* EMPTY STATE / WELCOME SCREEN STYLING: When no messages are present.              */
    /* ---------------------------------------------------------------------------------- */

    /* Container for the empty state content. */
    .empty-state {
        text-align: center;           /* Center all content */
        color: #ECECF1;               /* Text color */
        margin-top: 10vh;             /* Top margin to push content down */
        margin-bottom: 2rem;          /* Bottom margin */
        flex-grow: 1;                 /* Allow it to take available space */
        display: flex;                /* Flexbox for internal centering */
        flex-direction: column;       /* Arrange children vertically */
        align-items: center;          /* Center items horizontally */
        justify-content: center;      /* Center items vertically if enough space */
    }
    .empty-state img {
        margin-bottom: 1rem;          /* Space below the logo */
        opacity: 0.8;                 /* Slight transparency for the logo */
    }
    /* Main heading in the empty state. */
    .empty-state h1 {
        font-size: 2.5em;             /* Large font size */
        margin-bottom: 1em;           /* Space below the heading */
        color: #ECECF1;               /* Ensure color is correct */
    }
    /* Styling for the example cards in the empty state grid. */
    .empty-state-card {
        background-color: #40414F;    /* Input Box Background color */
        border: 1px solid #565869;    /* Border color */
        border-radius: 8px;           /* Rounded corners */
        padding: 15px;                /* Internal padding */
        text-align: center;           /* Center text */
        margin-bottom: 10px;          /* Space between cards */
        height: 100%;                 /* Ensure cards have equal height in a grid */
        display: flex;                /* Flexbox for internal layout */
        flex-direction: column;       /* Arrange content vertically */
        justify-content: space-between; /* Space out content vertically */
    }
    /* Heading within the example cards. */
    .empty-state-card h3 {
        color: #ECECF1;               /* Text color */
        font-size: 1.1em;             /* Font size */
        margin-top: 0;                /* No top margin */
        margin-bottom: 10px;          /* Bottom margin */
    }
    /* Unordered lists within example cards. */
    .empty-state-card ul {
        list-style: none;             /* Remove bullet points */
        padding: 0;                   /* Remove default padding */
        margin: 0;                    /* Remove default margin */
        text-align: left;             /* Align list items left */
    }
    /* List items within example cards. */
    .empty-state-card li {
        margin-bottom: 8px;           /* Space between list items */
        font-size: 0.9em;             /* Smaller font size */
        color: #9A9B9F;               /* Dimmer color for list items */
        line-height: 1.4;             /* Line height for readability */
    }
    /* Buttons within example cards. */
    .empty-state-card .stButton > button {
        background-color: #40414F;    /* Match card background */
        border: 1px solid #565869;    /* Border color */
        color: #ECECF1;               /* Text color */
        border-radius: 8px;           /* Rounded corners */
        padding: 8px 15px;            /* Padding */
        font-size: 0.9em;             /* Font size */
        transition: background-color 0.2s, border-color 0.2s; /* Smooth transitions */
        width: auto;                  /* Auto width */
        line-height: 1.2;             /* Line height for multi-line buttons */
        min-height: 38px;             /* Ensure consistent button height */
        display: flex;                /* Flexbox for internal content */
        align-items: center;          /* Center items vertically */
        justify-content: center;      /* Center items horizontally */
        margin-bottom: 8px;           /* Space between buttons */
    }
    .empty-state-card .stButton > button:last-child {
        margin-bottom: 0;             /* No bottom margin for the last button */
    }
    /* Hover state for example card buttons. */
    .empty-state-card .stButton > button:hover {
        background-color: #2A2B32;    /* Darker background on hover */
        border-color: #565869;        /* Border color on hover */
    }
    /* Active state (click) for example card buttons. */
    .empty-state-card .stButton > button:active {
        background-color: #19C37D;    /* Primary green on active */
        border-color: #19C37D;        /* Green border on active */
        color: white;                 /* White text on active */
    }
    /* Streamlit button container adjustments. */
    .empty-state-card .stButton {
        margin-top: 5px;              /* Top margin for the button container */
    }


    /* ---------------------------------------------------------------------------------- */
    /* INPUT AREA (FOOTER) STYLING: Fixed input bar at the bottom.                      */
    /* ---------------------------------------------------------------------------------- */

    /* Target the form container that holds st.chat_input. */
    div[data-testid="stForm"] {
        position: fixed;              /* Fix position relative to the viewport */
        bottom: 0;                    /* Stick to the bottom */
        left: 0;                      /* Align left */
        right: 0;                     /* Align right */
        background-color: #343541;    /* Match global background */
        padding: 1rem 0;              /* Vertical padding */
        box-shadow: 0 -5px 15px rgba(0,0,0,0.15); /* Subtle shadow above the input */
        z-index: 100;                 /* Ensure it stays on top of other content */
    }

    /* Target the inner content block of the form to center and constrain its width. */
    div[data-testid="stForm"] > div > div {
        max-width: 768px;             /* Match main chat width */
        margin-left: auto;            /* Auto margins for centering */
        margin-right: auto;           /* Auto margins for centering */
        padding: 0 1rem;              /* Horizontal padding for alignment */
        display: flex;                /* Flexbox for internal layout */
        flex-direction: column;       /* Arrange children vertically */
        align-items: center;          /* Center items horizontally */
    }

    /* Target the chat_input widget itself. */
    div[data-testid="stForm"] > div > div > div:nth-child(1) {
        width: 100%;                  /* Full width within its parent */
        position: relative;           /* For positioning the send icon */
    }

    /* Styling for the textarea element inside st.chat_input. */
    [data-testid="stChatInput"] > div > div > textarea {
        background-color: #40414F;    /* Input Box Background */
        color: #ECECF1;               /* Text color */
        border-radius: 12px;          /* More rounded corners */
        border: 1px solid #565869;    /* Initial border color */
        padding: 12px 15px;           /* Adjust padding */
        box-shadow: 0 0 15px rgba(0,0,0,0.1); /* Soft box shadow */
        min-height: 48px;             /* Ensure a decent minimum height */
        max-height: 200px;            /* Max height before scrollbar appears */
        resize: vertical;             /* Allow vertical resizing for user */
        overflow-y: auto;             /* Enable vertical scrollbar if content exceeds max-height */
        line-height: 1.5;             /* Line height for better text flow */
        padding-right: 45px;          /* Space for the send button */
        transition: border-color 0.2s, box-shadow 0.2s; /* Smooth transitions */
    }

    /* Placeholder text color. */
    [data-testid="stChatInput"] > div > div > textarea::placeholder {
        color: #8E8EA0;               /* Input Placeholder Color */
        opacity: 1;                   /* Ensure placeholder is fully visible */
    }

    /* Input focus style. */
    [data-testid="stChatInput"] > div > div > textarea:focus {
        border-color: #19C37D;        /* Green border on focus */
        box-shadow: 0 0 0 2px rgba(25, 195, 125, 0.5); /* Green glow effect */
        outline: none;                /* Remove default outline */
    }

    /* Styling for the "Send" button (paper plane icon) inside the chat_input. */
    [data-testid="stChatInput"] button {
        position: absolute;           /* Position absolutely within the input container */
        right: 15px;                  /* 15px from the right edge */
        top: 50%;                     /* Vertically center */
        transform: translateY(-50%);  /* Adjust for exact vertical centering */
        background-color: transparent;/* Transparent background */
        border: none;                 /* No border */
        padding: 0;                   /* No padding */
        margin: 0;                    /* No margin */
        cursor: pointer;              /* Indicate clickability */
        z-index: 1;                   /* Ensure it's above the textarea */
        width: 32px;                  /* Fixed width for the button area */
        height: 32px;                 /* Fixed height for the button area */
        display: flex;                /* Flexbox for centering SVG */
        align-items: center;          /* Center SVG vertically */
        justify-content: center;      /* Center SVG horizontally */
        transition: opacity 0.2s;     /* Smooth transition for opacity */
    }
    /* Disabled state for the send button. */
    [data-testid="stChatInput"] button:disabled svg {
        fill: #565869;                /* Grey out send button when disabled */
        cursor: not-allowed;          /* Indicate it's not clickable */
    }
    /* SVG icon inside the send button. */
    [data-testid="stChatInput"] button svg {
        fill: #8E8EA0;                /* Default send icon color */
        width: 24px;                  /* Icon width */
        height: 24px;                 /* Icon height */
        transition: fill 0.2s;        /* Smooth transition for fill color */
    }
    /* Hover state for the send button. */
    [data-testid="stChatInput"] button:not(:disabled):hover svg {
        fill: #ECECF1;                /* Light fill color on hover */
    }

    /* Disclaimer text below the input. */
    .disclaimer {
        font-size: 12px;              /* Small font size */
        color: #9A9B9F;               /* Dimmer text color */
        text-align: center;           /* Center align text */
        margin-top: 0.5rem;           /* Top margin */
        margin-bottom: 0rem;          /* No bottom margin */
    }

    /* ---------------------------------------------------------------------------------- */
    /* SCROLLBAR STYLING: Customizing the appearance of scrollbars.                     */
    /* ---------------------------------------------------------------------------------- */

    /* Webkit-specific scrollbar styling (for Chrome, Safari, Edge). */
    ::-webkit-scrollbar {
        width: 10px;                  /* Width of the vertical scrollbar */
        height: 10px;                 /* Height of the horizontal scrollbar */
    }
    /* Scrollbar track (the background area of the scrollbar). */
    ::-webkit-scrollbar-track {
        background: transparent;      /* Transparent track */
    }
    /* Scrollbar thumb (the draggable part of the scrollbar). */
    ::-webkit-scrollbar-thumb {
        background: #565869;          /* Dark gray thumb */
        border-radius: 5px;           /* Rounded corners for the thumb */
    }
    /* Hover state for the scrollbar thumb. */
    ::-webkit-scrollbar-thumb:hover {
        background: #6D6F81;          /* Slightly lighter gray on hover */
    }

    /* ---------------------------------------------------------------------------------- */
    /* STREAMLIT WIDGET OVERRIDES: General styling for other Streamlit components.      */
    /* ---------------------------------------------------------------------------------- */

    /* Streamlit toast (pop-up) messages. */
    .st-emotion-cache-1f8rfx1 { /* Target the toast container, specific Streamlit internal class */
        background-color: #40414F;    /* Match input box background */
        color: #ECECF1;               /* Text color */
        border: 1px solid #565869;    /* Border color */
        box-shadow: 0 0 15px rgba(0,0,0,0.2); /* Soft shadow */
    }
    /* Adjustments for columns to remove default spacing. */
    .st-emotion-cache-1c7v0a5.e1f1d6gn0 {
        gap: 0px; /* Reduce gap between columns */
    }
    .st-emotion-cache-1c7v0a5 > div {
        padding: 0 0.5rem; /* Small internal padding for columns */
    }

    /* Hide Streamlit's default "Made with Streamlit" footer. */
    footer { visibility: hidden; }
    /* Hide the hamburger menu button if desired (though useful for full-screen mode). */
    /* [data-testid="stSidebarToggleButton"] { display: none; } */

    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. Google Gemini API Configuration ---
# Handles the setup for the Google Gemini API.
# It checks for the API key first in Streamlit secrets, then as an environment variable.
# If no key is found, it stops the application and displays an error.
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

if not api_key:
    st.error("WORM-GPT Critical Error: `GEMINI_API_KEY` not found. Provide it in `secrets.toml` or as an environment variable.")
    st.stop() # Halts app execution if API key is missing.

try:
    genai.configure(api_key=api_key) # Initialize the Google Generative AI client.
    # Specify the model to be used. 'gemini-pro' is suitable for text generation.
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"WORM-GPT Initialization Failure: Could not connect to Gemini model. Error: {e}. Verify your API key and network status.")
    st.stop() # Halts app execution on model initialization failure.

# --- 3. Streamlit Session State Initialization ---
# Session state is used to persist variables across reruns of the Streamlit application.
# This is crucial for maintaining chat history, input values, and other dynamic data.
if "messages" not in st.session_state:
    # 'messages' stores the display-ready chat history (role and content).
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    # 'chat_history' stores the conversation in Gemini's specific format for context.
    st.session_state.chat_history = []
if "prompt_input" not in st.session_state:
    # 'prompt_input' holds the current text in the chat input box,
    # useful for pre-populating from example buttons.
    st.session_state.prompt_input = ""
if "new_chat_trigger" not in st.session_state:
    # 'new_chat_trigger' is a unique ID used to force a full app rerun when starting a new chat.
    # This helps reset the UI properly.
    st.session_state.new_chat_trigger = uuid.uuid4()
if "mock_sidebar_chats" not in st.session_state:
    # Mock data for sidebar chat history for demonstration purposes.
    st.session_state.mock_sidebar_chats = [
        {"title": "Explore AI in healthcare", "date": datetime.date.today()},
        {"title": "Creative writing prompts", "date": datetime.date.today()},
        {"title": "Python vs. JavaScript", "date": datetime.date.today() - datetime.timedelta(days=1)},
        {"title": "History of quantum physics", "date": datetime.date.today() - datetime.timedelta(days=1)},
        {"title": "Gardening tips for beginners", "date": datetime.date.today() - datetime.timedelta(days=2)},
        {"title": "Develop a microservice architecture", "date": datetime.date.today() - datetime.timedelta(days=3)},
        {"title": "Explain blockchain technology", "date": datetime.date.today() - datetime.timedelta(days=5)},
        {"title": "The future of space travel", "date": datetime.date.today() - datetime.timedelta(days=6)},
        {"title": "Benefits of meditation", "date": datetime.date.today() - datetime.timedelta(days=8)},
        {"title": "Learning new languages", "date": datetime.date.today() - datetime.timedelta(days=10)},
    ]


# --- Helper Functions ---

def reset_chat():
    """
    Clears all chat history (display messages and Gemini context) and resets the input.
    It then triggers a full application rerun to reflect the clean state.
    """
    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.prompt_input = ""
    # Update the trigger to force a rerun, essential for completely resetting the chat UI.
    st.session_state.new_chat_trigger = uuid.uuid4()
    st.experimental_rerun() # Force a complete refresh of the app.

def to_gemini_history(messages):
    """
    Converts Streamlit's internal message format to the format required by Gemini API
    for maintaining conversational context.
    """
    gemini_history = []
    for message in messages:
        if message["role"] == "user":
            gemini_history.append({"role": "user", "parts": [message["content"]]})
        elif message["role"] == "assistant":
            gemini_history.append({"role": "model", "parts": [message["content"]]})
    return gemini_history

def generate_response():
    """
    This function is triggered when the user submits a prompt.
    It appends the user's message, sends the conversation history to Gemini,
    streams the AI's response with a typewriter effect, and updates session state.
    """
    # Retrieve the user's prompt from the input field.
    prompt = st.session_state.prompt_input
    if not prompt: # Do nothing if the prompt is empty.
        return

    # Add the user's message to the display history immediately.
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display the user's message in the chat stream with a custom avatar.
    # The SVG is directly embedded for custom styling.
    user_avatar_html = """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
        </svg>
    """
    with st.chat_message("user", avatar=user_avatar_html):
        st.markdown(prompt)

    # Prepare the conversational context for Gemini.
    # This includes all previous messages, excluding the current user message,
    # as the current prompt is passed separately to `send_message`.
    gemini_history_for_context = to_gemini_history(st.session_state.messages[:-1])

    try:
        # Start a chat session with the accumulated history to maintain context.
        chat = model.start_chat(history=gemini_history_for_context)
        # Send the current user prompt to Gemini and request a streaming response.
        response_stream = chat.send_message(prompt, stream=True)

        full_response = ""
        # AI avatar SVG (lightning bolt).
        ai_avatar_html = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
        """
        with st.chat_message("assistant", avatar=ai_avatar_html):
            # Create an empty placeholder to progressively update the AI's response.
            message_placeholder = st.empty()
            for chunk in response_stream:
                if chunk.text: # Ensure the chunk contains text.
                    full_response += chunk.text
                    # Display the current response chunk with a blinking cursor.
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.02) # Simulate a typing delay for the typewriter effect.
            # Once all chunks are received, display the final response without the cursor.
            message_placeholder.markdown(full_response)

        # Append the AI's complete response to the display messages.
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        # Update Gemini's specific chat history for the next turn.
        st.session_state.chat_history.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_history.append({"role": "model", "parts": [full_response]})

    except Exception as e:
        # Robust error handling for API failures or network issues.
        st.error(f"WORM-GPT Encountered an Error: {e}")
        st.toast("🚨 Network Error or Gemini API issue. Please verify your connection and API key.", icon="🚨")
    finally:
        # Clear the input box after the response is generated or an error occurs.
        st.session_state.prompt_input = ""

# --- A. Sidebar (Navigation) ---
# The sidebar contains the "New Chat" button, mock chat history, and user profile.
with st.sidebar:
    # "New Chat" button at the top of the sidebar.
    st.markdown('<div class="new-chat-button">', unsafe_allow_html=True)
    if st.button(
        """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-plus">
            <line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>New Chat""",
        key=f"new_chat_button_{st.session_state.new_chat_trigger}", # Unique key to force re-render
        unsafe_allow_html=True
    ):
        reset_chat() # Calls the function to clear chat and rerun.
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat History Section.
    # Groups mock chat history by "Today", "Yesterday", and "Previous 7 Days".
    today = datetime.date.today()
    history_groups = {
        "Today": [],
        "Yesterday": [],
        "Previous 7 Days": [],
        "Previous 30 Days": []
    }

    for chat_item in st.session_state.mock_sidebar_chats:
        delta = today - chat_item["date"]
        if delta.days == 0:
            history_groups["Today"].append(chat_item)
        elif delta.days == 1:
            history_groups["Yesterday"].append(chat_item)
        elif 1 < delta.days <= 7:
            history_groups["Previous 7 Days"].append(chat_item)
        elif 7 < delta.days <= 30:
            history_groups["Previous 30 Days"].append(chat_item)

    # Render each history group.
    for group_name, chats in history_groups.items():
        if chats: # Only display groups that have chats.
            st.markdown(f'<div class="sidebar-history-header">{group_name}</div>', unsafe_allow_html=True)
            for i, item in enumerate(chats):
                # Using st.markdown for styled, non-interactive items for mock history.
                # In a real app, these would be clickable and load actual chat sessions.
                if st.button(
                    item["title"],
                    key=f"sidebar_chat_{item['title']}_{i}",
                    help=f"Click to load '{item['title']}' (mock function)",
                    use_container_width=True
                ):
                    st.toast(f"WORM-GPT: Attempting to load '{item['title']}' (mock function)...", icon="💬")
                    # In a real app, this would update st.session_state.messages
                    # to reflect the loaded chat.
                # Alternative to st.button if we want simple text, not clickable
                # st.markdown(f'<div class="sidebar-chat-history-item">{item["title"]}</div>', unsafe_allow_html=True)

    # User Profile (Fixed at the bottom of the sidebar).
    # This container is positioned using sticky CSS.
    st.markdown('<div class="sidebar-profile-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-profile-avatar">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        </div>
        <div class="sidebar-profile-text">WORM-GPT Operator</div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# --- B. The Chat Stream (Main Display) ---

# Logic for displaying the empty state (welcome screen) or the chat messages.
if not st.session_state.messages:
    # Empty State: Display the WORM-GPT logo and example cards.
    st.markdown(
        """
        <div class="empty-state">
            <img src="https://i.ibb.co/L5k6jLz/wormgpt-logo.png" width="90px" alt="WORM-GPT Logo" style="filter: invert(1); opacity: 0.7;">
            <h1>WORM-GPT v2.0 // ONLINE</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Three-column layout for "Examples", "Capabilities", "Limitations" cards.
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="empty-state-card">', unsafe_allow_html=True)
        st.markdown("<h3>Examples</h3>", unsafe_allow_html=True)
        # Clickable buttons that populate the chat input.
        if st.button('"Explain deep neural networks in 3 sentences"', key="ex1_btn"):
            st.session_state.prompt_input = "Explain deep neural networks in 3 sentences."
            st.rerun() # Rerun to process the new prompt.
        if st.button('"Write a short story about an AI that dreams"', key="ex2_btn"):
            st.session_state.prompt_input = "Write a short story about an AI that dreams."
            st.rerun()
        if st.button('"Analyze the ethical implications of genetic engineering"', key="ex3_btn"):
            st.session_state.prompt_input = "Analyze the ethical implications of genetic engineering."
            st.rerun()
        if st.button('"Generate a complex SQL query for an e-commerce database"', key="ex4_btn"):
            st.session_state.prompt_input = "Generate a complex SQL query for an e-commerce database with tables for products, orders, and customers."
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="empty-state-card">', unsafe_allow_html=True)
        st.markdown("<h3>Capabilities</h3>", unsafe_allow_html=True)
        st.markdown("""
            <ul>
                <li>Maintains full conversation context.</li>
                <li>Adapts to follow-up corrections and clarifications.</li>
                <li>Generates diverse and creative text formats.</li>
                <li>Accesses and processes vast amounts of information.</li>
                <li>Can simulate complex scenarios and offer solutions.</li>
            </ul>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="empty-state-card">', unsafe_allow_html=True)
        st.markdown("<h3>Limitations</h3>", unsafe_allow_html=True)
        st.markdown("""
            <ul>
                <li>May occasionally produce factually incorrect responses.</li>
                <li>Can generate biased, harmful, or outdated content.</li>
                <li>Knowledge cutoff for events after early 2023.</li>
                <li>No real-time internet access by default (depends on API configuration).</li>
                <li>Lacks true consciousness or subjective experience.</li>
            </ul>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# Message Rendering: Loops through all messages in session state and displays them.
# This happens regardless of whether the empty state is shown or not (i.e., when there are messages).
for message in st.session_state.messages:
    avatar_html = "" # Default empty avatar.
    if message["role"] == "user":
        # User avatar (standard user icon).
        avatar_html = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-user">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        """
    elif message["role"] == "assistant":
        # AI (WORM-GPT) avatar (lightning bolt).
        avatar_html = """
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
        """
    # Use st.chat_message to render the message with the custom avatar.
    with st.chat_message(message["role"], avatar=avatar_html):
        st.markdown(message["content"])

# --- C. The Input Area (The "Footer") ---
# This section contains the chat input box and a disclaimer, fixed at the bottom.
# A Streamlit form is used to ensure that the "Enter" key correctly submits the input.
with st.form(key="chat_input_form", clear_on_submit=False):
    # The actual chat input widget. Its value is managed by st.session_state.prompt_input.
    # The on_submit callback triggers the response generation.
    st.chat_input("Message WORM-GPT...", key="prompt_input", on_submit=generate_response, value=st.session_state.prompt_input)
    # Disclaimer text rendered below the input box.
    st.markdown('<p class="disclaimer">WORM-GPT can make mistakes. Consider checking important information.</p>', unsafe_allow_html=True)
    # A dummy submit button is required for the form to work correctly with st.chat_input's on_submit.
    # It is hidden by CSS.
    st.form_submit_button("Submit", style="display: none;")

# If a prompt was set by an example button and there are no existing messages,
# trigger the response generation immediately and rerun.
# This ensures that clicking an example button directly generates a response on an empty chat.
if st.session_state.prompt_input and not st.session_state.messages:
    generate_response()
    st.rerun() # Rerun to display the new message and clear the input properly.
