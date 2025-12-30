import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-wormgpt-super-secret-key-replace-me-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://neondb_owner:npg_fROhe2Y3CWoH@ep-crimson-darkness-ahs5m622-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API Keys (Use multiple if you have them, or manage tiers with one key)
    GEMINI_API_KEY_FREE = os.environ.get('GEMINI_API_KEY_FREE') # e.g., for gemini-1.5-flash
    GEMINI_API_KEY_PRO = os.environ.get('GEMINI_API_KEY_PRO')   # e.g., for gemini-1.5-pro
    GEMINI_API_KEY_VIP = os.environ.get('GEMINI_API_KEY_VIP')   # e.g., for gemini-1.5-pro with higher limits/optimizations

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    GOOGLE_TOKEN_URI = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URI = 'https://www.googleapis.com/oauth2/v1/userinfo'
    # This redirect URI must be registered in your Google Cloud Console
    # For local testing, it might be http://localhost:5000/api/auth/google/callback
    # For production, it will be https://your-domain.com/api/auth/google/callback
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

    # Storage for uploaded files (e.g., for Vision API)
    UPLOAD_FOLDER = 'uploads' # Relative to backend directory
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload size
