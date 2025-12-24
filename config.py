"""
EduMate Configuration Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'edumate-dev-secret-key'
    
    # Application settings
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Database settings (SQLite)
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edumate_local.db')
    
    # Security settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'}
    
    # Pagination
    ITEMS_PER_PAGE = 12
    
    # Recommendation settings
    RECOMMENDATION_CACHE_TIME = 3600  # 1 hour
    MAX_RECOMMENDATIONS = 20

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or Config.DATABASE_PATH

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edumate_test.db')
    WTF_CSRF_ENABLED = False

# Dictionary to map configuration names to configuration classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}