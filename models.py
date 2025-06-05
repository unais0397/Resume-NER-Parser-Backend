from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import bcrypt
import secrets
import string

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verification_codes = db.relationship('VerificationCode', backref='user', lazy=True, cascade='all, delete-orphan')
    resumes = db.relationship('Resume', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the password"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.Text)  # Base64 PDF data
    entities = db.Column(db.JSON)   # Extracted entities as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert resume object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'entities': self.entities or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Resume {self.filename} for user {self.user_id}>'

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    code_type = db.Column(db.String(20), nullable=False)  # 'email_verification', 'password_reset', etc.
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, code_type='email_verification', expiry_minutes=3):
        self.user_id = user_id
        self.code_type = code_type
        self.code = self.generate_code()
        self.expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_expired(self):
        """Check if the verification code has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if the code is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark the verification code as used"""
        self.is_used = True
        db.session.commit()
    
    def to_dict(self):
        """Convert verification code object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'code': self.code,
            'code_type': self.code_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_used': self.is_used,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid()
        }
    
    def __repr__(self):
        return f'<VerificationCode {self.code} for user {self.user_id}>' 