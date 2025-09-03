import os
from datetime import timedelta

class Config:
    """Configuration de base de l'application"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # Utiliser SQLite temporairement pour tester
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///meet.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration des uploads
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Configuration des messages et notifications éphémères
    MESSAGE_EXPIRY_HOURS = 24
    NOTIFICATION_EXPIRY_HOURS = 24
    
    # Configuration de la pagination
    PROFILES_PER_PAGE = 12
    
    # Configuration des filtres
    MIN_AGE = 18
    MAX_AGE = 100
    
    # Configuration des centres d'intérêt
    INTERESTS = [
        'Sport', 'Musique', 'Voyage', 'Cuisine', 'Art', 'Lecture', 
        'Cinéma', 'Nature', 'Technologie', 'Mode', 'Photographie', 
        'Danse', 'Théâtre', 'Jeux vidéo', 'Yoga', 'Méditation'
    ]

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # En production, utiliser des clés sécurisées
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Dictionnaire des configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
