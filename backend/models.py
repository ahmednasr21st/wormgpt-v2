from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for stronger hashes
    google_id = db.Column(db.String(120), unique=True, nullable=True) # For Google OAuth
    plan = db.Column(db.String(50), default='free') # 'free', 'pro', 'vip'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Chat sessions
    chats = db.relationship('Chat', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), default='New Chat')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to Messages
    messages = db.relationship('Message', backref='chat', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Chat {self.id} by User {self.user_id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'user' or 'ai'
    content = db.Column(db.Text, nullable=False)
    # Store file paths or references if needed for image input with AI
    file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} ({self.role}) in Chat {self.chat_id}>'
