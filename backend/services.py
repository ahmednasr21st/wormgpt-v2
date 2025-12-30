import google.generativeai as genai
from flask import current_app
import os
import mimetypes

def configure_gemini_api(api_key):
    """Configures the Gemini API with the given API key."""
    genai.configure(api_key=api_key)

def get_gemini_model_config(user_plan):
    """
    Returns the appropriate Gemini model and API key based on the user's plan.
    Also includes a mock "strength" score.
    """
    free_api_key = current_app.config['GEMINI_API_KEY_FREE']
    pro_api_key = current_app.config['GEMINI_API_KEY_PRO']
    vip_api_key = current_app.config['GEMINI_API_KEY_VIP']

    if user_plan == 'vip':
        # VIP uses 1.5 Pro with highest settings/context window
        return {
            'api_key': vip_api_key or pro_api_key or free_api_key, # Fallback
            'model_name': 'gemini-1.5-pro-latest',
            'generation_config': {
                "temperature": 0.9,
                "top_p": 1,
                "top_k": 32,
                "max_output_tokens": 4096, # Very high token limit
            },
            'safety_settings': [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
            'strength': 5 # Max strength
        }
    elif user_plan == 'pro':
        # Pro uses 1.5 Pro with good settings
        return {
            'api_key': pro_api_key or free_api_key, # Fallback
            'model_name': 'gemini-1.5-pro-latest',
            'generation_config': {
                "temperature": 0.8,
                "top_p": 0.95,
                "top_k": 28,
                "max_output_tokens": 2048, # High token limit
            },
            'safety_settings': [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_FEW"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_FEW"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_FEW"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_FEW"},
            ],
            'strength': 3 # Moderate strength
        }
    else: # 'free' plan
        # Free uses 1.5 Flash with basic settings
        return {
            'api_key': free_api_key,
            'model_name': 'gemini-1.5-flash-latest', # Use the flash model for free tier
            'generation_config': {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 20,
                "max_output_tokens": 512, # Limited token output
            },
            'safety_settings': [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
            'strength': 1 # Simple strength
        }

def get_mime_type(file_path):
    """Guesses the MIME type of a file based on its extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    # Fallback for common types if guess_type fails
    if file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        return 'image/jpeg' # Or specific image type
    return 'application/octet-stream' # Generic binary

def process_file_for_gemini(file_paths):
    """
    Processes a list of file paths into Gemini-compatible parts.
    Currently supports image files for Gemini Vision.
    """
    parts = []
    for file_path in file_paths:
        mime_type = get_mime_type(file_path)
        if mime_type and mime_type.startswith('image/'):
            with open(file_path, 'rb') as f:
                parts.append({
                    'mime_type': mime_type,
                    'data': f.read()
                })
        else:
            # For other file types, you'd need advanced parsing (e.g., text extraction)
            # For now, we'll just add a placeholder text reference if not an image
            current_app.logger.warning(f"Unsupported file type for Gemini Vision: {file_path} ({mime_type}). Skipping image analysis.")
            parts.append(f"File content: (Path: {os.path.basename(file_path)} - This file type requires specific parsing not yet implemented for direct AI vision).")
    return parts


def generate_ai_response(user_plan, chat_messages, uploaded_files_paths=None):
    """
    Generates an AI response based on the chat history and user plan.
    Handles multimodal input (text + images).
    `chat_messages` should be a list of {'role': 'user'|'model', 'parts': [text/image_data]}
    """
    model_config = get_gemini_model_config(user_plan)
    configure_gemini_api(api_key=model_config['api_key'])

    model = genai.GenerativeModel(model_config['model_name'])

    # Prepare history for the model
    # Gemini's chat history expects alternating user/model roles.
    # We might need to adjust or reformat if our DB history isn't perfectly alternating.
    # For now, assume chat_messages is already formatted from DB.
    # Gemini also requires 'parts' for content, even if just text.
    formatted_history = []
    for msg in chat_messages:
        parts = []
        if isinstance(msg['content'], str):
            parts.append(msg['content'])
        else: # Assuming content might be a list of parts already
            parts.extend(msg['content'])

        formatted_history.append({'role': msg['role'], 'parts': parts})

    # Prepare the actual content for the current turn (last user message + files)
    contents_for_current_turn = []

    # Add the last user message content
    if formatted_history and formatted_history[-1]['role'] == 'user':
        contents_for_current_turn.extend(formatted_history[-1]['parts'])
        # Remove the last user message from history, as it's part of current turn
        formatted_history = formatted_history[:-1]


    # Add processed files if any
    if uploaded_files_paths and user_plan in ['pro', 'vip']: # Only Pro/VIP can process files
        file_parts = process_file_for_gemini(uploaded_files_paths)
        if file_parts:
            contents_for_current_turn.extend(file_parts)
            # Prepend a prompt if only files are uploaded without text
            if not contents_for_current_turn[0]: # If first part is empty string from message
                contents_for_current_turn[0] = "Analyze the provided files and respond accordingly."
    elif uploaded_files_paths and user_plan == 'free':
        current_app.logger.info("File upload attempted by free user, skipping AI processing for files.")
        contents_for_current_turn.append("Note: File processing is a Pro/VIP feature. I will respond to text only.")

    if not contents_for_current_turn:
        return "No content provided to the AI."


    try:
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(
            contents_for_current_turn,
            generation_config=model_config['generation_config'],
            safety_settings=model_config['safety_settings']
        )
        return response.text
    except Exception as e:
        current_app.logger.error(f"Gemini API error: {e}")
        return f"AI communication error: {str(e)}. Please check API key and model access."
