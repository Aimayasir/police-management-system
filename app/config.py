import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

def get_secret_key():
    secret_key = os.environ.get('SECRET_KEY')
    env_mode = (os.environ.get('FLASK_ENV') or os.environ.get('ENV') or 'development').lower()
    is_prod = env_mode == 'production' or os.environ.get('PRODUCTION', '').lower() in ('true', '1')

    if is_prod:
        if not secret_key:
            raise ValueError(
                "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is missing in production mode. "
                "Please configure SECRET_KEY in your Render dashboard environment variables."
            )
        return secret_key

    # Harmless dev-only fallback when FLASK_ENV is development
    return secret_key or 'dev-insecure-secret-key-change-in-production'

def get_database_uri():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return f"sqlite:///{BASE_DIR / 'instance' / 'psms.db'}"
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    elif db_url == 'sqlite:///instance/psms.db':
        return f"sqlite:///{BASE_DIR / 'instance' / 'psms.db'}"
    return db_url

class Config:
    SECRET_KEY = get_secret_key()
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 10))
    UPLOAD_FOLDER = BASE_DIR / 'instance' / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # 30-minute inactivity session timeout
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt'}

    # Session cookie security settings for production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = (
        (os.environ.get('FLASK_ENV') or os.environ.get('ENV') or '').lower() == 'production'
        or os.environ.get('PRODUCTION', '').lower() in ('true', '1')
    )
