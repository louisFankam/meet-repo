"""
Application principale Meet
Point d'entrée avec structure MVC
"""

import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv
from model.extensions import init_extensions
from model.database import db
from controller.routes import register_routes, register_filters
from model.services import InterestService

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def create_app(config_object=None):
    """Usine d'application Flask"""
    app = Flask(__name__)
    
    # Configuration
    if config_object:
        app.config.from_object(config_object)
    else:
        # Configuration par défaut
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///meet.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = 'static/uploads'
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # Initialiser les extensions
    init_extensions(app)
    
    # Désactiver CSRF protection
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Force reload to pick up .env changes
    if 'DATABASE_URL' in os.environ:
        print(f"Database URL from env: {os.environ['DATABASE_URL']}")
    
    # Enregistrer les routes et filtres
    register_routes(app)
    register_filters(app)
    
    # Configuration des templates
    app.template_folder = 'template'
    
    with app.app_context():
        db.create_all()
        InterestService.initialize_default_interests()
    
    logger.info("Application Meet créée avec succès")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)