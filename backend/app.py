import os
from flask import Flask, request, jsonify, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from requests_oauthlib import OAuth2Session
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import google.generativeai as genai  # إضافة المكتبة الناقصة هنا

# Local imports
from config import Config
from models import db, User, Chat, Message
from services import generate_ai_response, get_gemini_model_config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
# تأكد من تعديل origins لتشمل دومينك لاحقاً
CORS(app, supports_credentials=True) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_bp.login'

# Ensure UPLOAD_FOLDER exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Initialization ---
with app.app_context():
    db.create_all()
    print("Database tables created/checked.")

# --- API Endpoints ---

# --- Authentication (auth_bp) ---
from flask import Blueprint
auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Missing username, email, or password'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        user = User.query.filter_by(email=username).first()
        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid credentials'}), 401

    login_user(user)
    return jsonify({
        'message': 'Logged in successfully!', 
        'username': user.username, 
        'plan': user.plan, 
        'access_token': session.sid
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

# Google OAuth routes
@auth_bp.route('/google')
def google_login():
    google = OAuth2Session(app.config['GOOGLE_CLIENT_ID'], 
                           scope=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
                           redirect_uri=app.config['GOOGLE_REDIRECT_URI'])
    authorization_url, state = google.authorization_url(app.config['GOOGLE_AUTH_URI'], access_type='offline', prompt='select_account')
    session['oauth_state'] = state
    return redirect(authorization_url)

@auth_bp.route('/google/callback')
def google_callback():
    if 'error' in request.args:
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        app.logger.error(f"Google OAuth error: {error} - {error_description}")
        return redirect(url_for('frontend_error_page', error_msg="Google login failed: " + error_description))

    if 'code' not in request.args or 'oauth_state' not in session or session['oauth_state'] != request.args.get('state'):
        app.logger.error("Google OAuth callback: Missing code or state mismatch.")
        return redirect(url_for('frontend_error_page', error_msg="Google login failed: Security error."))

    google = OAuth2Session(app.config['GOOGLE_CLIENT_ID'], state=session['oauth_state'],
                           redirect_uri=app.config['GOOGLE_REDIRECT_URI'])
    try:
        token = google.fetch_token(app.config['GOOGLE_TOKEN_URI'], client_secret=app.config['GOOGLE_CLIENT_SECRET'],
                                   authorization_response=request.url)
        session['google_token'] = token

        user_info = google.get(app.config['GOOGLE_USERINFO_URI']).json()
        google_id = user_info['id']
        email = user_info['email']
        username = user_info['name']

        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            existing_user_by_email = User.query.filter_by(email=email).first()
            if existing_user_by_email:
                existing_user_by_email.google_id = google_id
                db.session.commit()
                user = existing_user_by_email
            else:
                user = User(google_id=google_id, email=email, username=username)
                db.session.add(user)
                db.session.commit()
        login_user(user)
        # ملاحظة: قم بتغيير localhost إلى wormgpt.site عند الربط النهائي
        return redirect('http://localhost:3000/chat.html') 
    except Exception as e:
        app.logger.error(f"Google OAuth token/userinfo error: {e}")
        return redirect(url_for('frontend_error_page', error_msg="Google login failed due to an internal error."))

@app.route('/error')
def frontend_error_page():
    error_msg = request.args.get('error_msg', 'An unknown error occurred.')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <style>
            body {{ font-family: sans-serif; background-color: #1a1a2e; color: #e0e0e0; text-align: center; padding-top: 50px; }}
            .container {{ background-color: #22223b; padding: 30px; border-radius: 10px; display: inline-block; }}
            h1 {{ color: #ff4757; }}
            a {{ color: #4a90e2; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Error</h1>
            <p>{error_msg}</p>
            <p><a href="http://localhost:3000/index.html">Go back to login</a></p>
        </div>
    </body>
    </html>
    """

app.register_blueprint(auth_bp)

# --- User & Chat Management Endpoints ---

def auth_required_decorator(f):
    @login_required
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/user/profile', methods=['GET'])
@auth_required_decorator
def get_user_profile():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'plan': current_user.plan
    }), 200

@app.route('/api/user/plan', methods=['GET'])
@auth_required_decorator
def get_user_plan(): # التأكد من أن الاسم فريد لمنع AssertionError
    return jsonify({'plan_model': current_user.plan}), 200

@app.route('/api/user/subscribe', methods=['POST'])
@auth_required_decorator
def subscribe_user():
    data = request.get_json()
    plan = data.get('plan')
    if plan not in ['pro', 'vip']:
        return jsonify({'message': 'Invalid plan specified'}), 400
    current_user.plan = plan
    db.session.commit()
    return jsonify({'message': f'Subscription to {plan.upper()} plan successful!', 'new_plan': plan}), 200

@app.route('/api/chat/history', methods=['GET'])
@auth_required_decorator
def get_chat_history():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
    return jsonify([{'id': chat.id, 'title': chat.title, 'created_at': chat.created_at} for chat in chats]), 200

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
@auth_required_decorator
def get_chat_messages(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'message': 'Chat not found or unauthorized'}), 404
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at).all()
    formatted_messages = []
    for msg in messages:
        content_parts = []
        if msg.file_path:
            content_parts.append(f"![Uploaded Image]({url_for('uploaded_file', filename=os.path.basename(msg.file_path))})")
        content_parts.append(msg.content)
        formatted_messages.append({
            'id': msg.id,
            'role': msg.role,
            'content': " ".join(content_parts).strip(),
            'created_at': msg.created_at
        })
    return jsonify(formatted_messages), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/chat/send', methods=['POST'])
@auth_required_decorator
def send_message():
    message_text = request.form.get('message', '').strip()
    chat_id = request.form.get('chat_id', None)
    uploaded_files = request.files.getlist('files')

    if not message_text and not uploaded_files:
        return jsonify({'message': 'No message text or files provided'}), 400

    current_chat = None
    if chat_id:
        current_chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if not current_chat:
            return jsonify({'message': 'Chat not found or unauthorized'}), 404
    else:
        current_chat = Chat(user_id=current_user.id, title="New Chat")
        db.session.add(current_chat)
        db.session.commit()

    file_paths = []
    if current_user.plan in ['pro', 'vip'] and uploaded_files:
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                file_paths.append(file_path)
    elif uploaded_files:
        message_text += "\n\n(Note: File attachments are a Pro/VIP feature and were not processed.)"

    user_message = Message(chat_id=current_chat.id, role='user', content=message_text, file_path=file_paths[0] if file_paths else None)
    db.session.add(user_message)
    current_chat.updated_at = datetime.utcnow()
    db.session.commit()

    chat_history = Message.query.filter_by(chat_id=current_chat.id).order_by(Message.created_at).all()
    formatted_history = [{'role': msg.role, 'content': msg.content} for msg in chat_history]

    try:
        ai_response_text = generate_ai_response(current_user.plan, formatted_history, file_paths)
    except Exception as e:
        app.logger.error(f"Error generating AI response: {e}")
        ai_response_text = "Apologies, an internal error occurred while processing your request."

    ai_message = Message(chat_id=current_chat.id, role='ai', content=ai_response_text)
    db.session.add(ai_message)

    if current_chat.title == "New Chat":
        try:
            title_gen_config = get_gemini_model_config('free')
            genai.configure(api_key=title_gen_config['api_key'])
            title_model = genai.GenerativeModel(title_gen_config['model_name'])
            title_response = title_model.generate_content(
                f"Create a concise 5-word chat title for this user message: '{message_text}'",
                generation_config={"max_output_tokens": 20, "temperature": 0.5},
                safety_settings=title_gen_config['safety_settings']
            )
            current_chat.title = title_response.text.replace('"', '').strip()[:200]
            db.session.commit()
        except Exception as e:
            current_chat.title = message_text[:50] + "..." if len(message_text) > 50 else message_text
            db.session.commit()

    return jsonify({
        'chat_id': current_chat.id,
        'chat_title': current_chat.title,
        'response': ai_response_text
    }), 200

@app.route('/api/chat/<int:chat_id>/title', methods=['PUT'])
@auth_required_decorator
def update_chat_title(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'message': 'Chat not found or unauthorized'}), 404
    data = request.get_json()
    new_title = data.get('title')
    if not new_title:
        return jsonify({'message': 'New title is required'}), 400
    chat.title = new_title[:200]
    db.session.commit()
    return jsonify({'message': 'Chat title updated', 'new_title': chat.title}), 200

@app.route('/api/chat/<int:chat_id>', methods=['DELETE'])
@auth_required_decorator
def delete_chat(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat:
        return jsonify({'message': 'Chat not found or unauthorized'}), 404
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'message': 'Chat deleted successfully'}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
