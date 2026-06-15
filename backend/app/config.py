import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    DATABASE = 'attendance.db'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE = 'attendance.db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DATABASE = os.getenv('DATABASE_URL', 'attendance.db')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}