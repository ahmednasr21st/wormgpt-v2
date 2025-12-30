import os
from flask import Flask, request, jsonify, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from requests_oauthlib import OAuth2Session
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import google.generativeai as genai  # تم إضافة الاستيراد الناقص لضمان عمل Gemini

# Local imports
from config import Config
from models import db, User, Chat, Message
from services import generate_ai_response, get_gemini_model_config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
# السماح بمرور البيانات بين الدومين والباك إند
CORS(app, supports_credentials=True) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_bp.login'

# التأكد من وجود مجلد الرفع
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Initialization ---
with app.app_context():
    db.create_all()
    print("Database tables created/checked.")

# --- Authentication Blueprint ---
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
        return redirect(url_for('frontend_error_page', error_msg="Google login failed."))

    if 'code' not in request.args or 'oauth_state' not in session or session['oauth_state'] != request.args.get('state'):
        return redirect(url_for('frontend_error_page', error_msg="Security error."))

    google = OAuth2Session(app.config['GOOGLE_CLIENT_ID'], state=session['oauth_state'],
                           redirect_uri=app.config['GOOGLE_REDIRECT_URI'])
    try:
        token = google.fetch_token(app.config['GOOGLE_TOKEN_URI'], client_secret=app.config['GOOGLE_CLIENT_SECRET'],
                                   authorization_response=request.url)
        session['google_token'] = token
        user_info = google.get(app.config['GOOGLE_USERINFO_URI']).json()
        
        user = User.query.filter_by(google_id=user_info['id']).first()
        if not user:
            user = User(google_id=user_info['id'], email=user_info['email'], username=user_info['name'])
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        # سيتم تغيير localhost إلى wormgpt.site لاحقاً
        return redirect('http://localhost:3000/chat.html') 
    except Exception as e:
        return redirect(url_for('frontend_error_page', error_msg=str(e)))

@app.route('/error')
def frontend_error_page():
    return "<h1>Error Occurred</h1><a href='/'>Go Back</a>"

app.register_blueprint(auth_bp)

# --- Management Endpoints ---

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
def get_user_plan(): # تم تغيير الاسم هنا من get_user_profile لمنع الـ AssertionError
    return jsonify({'plan_model': current_user.plan}), 200

@app.route('/api/user/subscribe', methods=['POST'])
@auth_required_decorator
def subscribe_user():
    data = request.get_json()
    plan = data.get('plan')
    if plan not in ['pro', 'vip']:
        return jsonify({'message': 'Invalid plan'}), 400
    current_user.plan = plan
    db.session.commit()
    return jsonify({'message': 'Success', 'new_plan': plan}), 200

@app.route('/api/chat/history', methods=['GET'])
@auth_required_decorator
def get_chat_history():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.updated_at.desc()).all()
    return jsonify([{'id': chat.id, 'title': chat.title} for chat in chats]), 200

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
@auth_required_decorator
def get_chat_messages(chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if not chat: return jsonify({'message': 'Not found'}), 404
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at).all()
    return jsonify([{'role': m.role, 'content': m.content} for m in messages]), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/chat/send', methods=['POST'])
@auth_required_decorator
def send_message():
    message_text = request.form.get('message', '').strip()
    chat_id = request.form.get('chat_id', None)
    
    if not chat_id:
        current_chat = Chat(user_id=current_user.id, title="New Chat")
        db.session.add(current_chat)
        db.session.commit()
    else:
        current_chat = Chat.query.get(chat_id)

    user_message = Message(chat_id=current_chat.id, role='user', content=message_text)
    db.session.add(user_message)
    db.session.commit()

    try:
        # استدعاء الخدمة لتوليد رد الذكاء الاصطناعي
        ai_response = generate_ai_response(current_user.plan, [{'role': 'user', 'content': message_text}])
        ai_message = Message(chat_id=current_chat.id, role='ai', content=ai_response)
        db.session.add(ai_message)
        db.session.commit()
        return jsonify({'response': ai_response, 'chat_id': current_chat.id}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port))
