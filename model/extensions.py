"""
Extensions Flask pour l'application Meet
Initialise toutes les extensions nécessaires
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from datetime import datetime, timezone
import os

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('meet.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialisation des extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "200 per hour"]
)


def init_extensions(app):
    """Initialise toutes les extensions avec l'application"""
    
    # Configuration de la base de données (ne pas écraser la configuration existante)
    if 'SQLALCHEMY_DATABASE_URI' not in app.config:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost/meet_db')
    if 'SQLALCHEMY_TRACK_MODIFICATIONS' not in app.config:
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuration des uploads
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Créer le dossier uploads s'il n'existe pas
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Configuration de Flask-Login
    login_manager.login_view = 'login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Configuration de la clé secrète
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Définir le user_loader
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'utilisateur {user_id}: {e}")
            return None
    
    # S'assurer que la session de base de données est propre après chaque requête
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    # Rendre le CSRF token disponible dans tous les templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)
    
    logger.info("Extensions initialisées avec succès")
    
    return app


def get_timezone_aware_datetime():
    """Retourne une datetime avec fuseau horaire UTC"""
    return datetime.now(timezone.utc)