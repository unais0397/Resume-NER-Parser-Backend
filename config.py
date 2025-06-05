import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File storage configuration
RAW_FOLDER = os.path.join(BASE_DIR, "raw_pdfs")
CLEAN_FOLDER = os.path.join(BASE_DIR, "clean_text")
BLURR_FOLDER = os.path.join(BASE_DIR, "blurred_docs")

# Logging configuration
LOG_FILE = os.path.join(BASE_DIR, "application.log")

# Application settings
PORT = int(os.getenv('PORT', 8002))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {'application/pdf'}

# Text processing parameters
MIN_TEXT_LENGTH = 100  # Minimum characters to consider valid

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/resume_ner_db')
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

# Email configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

# Verification code settings
VERIFICATION_CODE_EXPIRY = 180  # 3 minutes in seconds