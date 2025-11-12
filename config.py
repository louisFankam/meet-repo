"""
Configuration pour la production
Variables et paramètres spécifiques à l'environnement de production
"""

import os
from datetime import timedelta

class ProductionConfig:
    """Configuration de production"""
    
    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY est requis en production")
    
    # Database - Utilisation des variables d'environnement centralisées
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME')
    
    # Vérification des variables BDD obligatoires
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
        raise ValueError("Variables de base de données manquantes: DB_USER, DB_PASSWORD, DB_HOST, DB_NAME")
    
    # Construction automatique de l'URI BDD
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        os.environ.get('DATABASE_URL') or \
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Upload et fichiers
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Session Flask
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Messages temporaires
    MESSAGE_EXPIRY_HOURS = 24
    NOTIFICATION_EXPIRY_HOURS = 48
    
    # Performance
    PROFILES_PER_PAGE = 12
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Désactiver les fonctionnalités de debug
    DEBUG = False
    TESTING = False
    
    # Sécurité CSRF
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = True
    
    # Headers de sécurité
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }


class DevelopmentConfig:
    """Configuration de développement"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database - Utilisation des variables d'environnement centralisées avec fallback
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'meet_db')
    
    # Construction de l'URI BDD
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        os.environ.get('DATABASE_URL') or \
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    DEBUG = True
    TESTING = False


# Dictionnaire de configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}