"""
Application principale Meet
Point d'entrée avec structure MVC
"""

import os
import sys
import logging
from flask import Flask
from dotenv import load_dotenv

# charger .env tôt
load_dotenv()

# importer les extensions correctement
from model.extensions import init_extensions, db

from controller.routes import register_routes, register_filters
from model.services import InterestService
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Scheduler pour le nettoyage automatique
scheduler = BackgroundScheduler()

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

        # Priorité: SQLALCHEMY_DATABASE_URI > DATABASE_URL > construction à partir des composants
        uri = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL')
        if not uri:
            user = os.getenv('DATABASE_USER', 'root')
            password = os.getenv('DATABASE_PASSWORD', '')  # mettre le mot de passe dans .env
            host = os.getenv('DATABASE_HOST', 'localhost')
            name = os.getenv('DATABASE_NAME', 'meet_db')
            uri = f"mysql+pymysql://{user}:{password}@{host}/{name}"
        app.config['SQLALCHEMY_DATABASE_URI'] = uri

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = 'static/uploads'
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # Initialiser les extensions
    init_extensions(app)
    
    # Enregistrer les routes et filtres
    register_routes(app)
    register_filters(app)
    
    # Configuration des templates
    app.template_folder = 'template'
    
    with app.app_context():
        try:
            db.create_all()
            InterestService.initialize_default_interests()
        except Exception as e:
            logger.error("Impossible de créer les tables au démarrage: %s", e)
            # Ne pas crash pour permettre debug de configuration DB
    
    # Fonction de nettoyage automatique planifiée
    def scheduled_cleanup():
        with app.app_context():
            try:
                from model.services import cleanup_expired_messages, cleanup_expired_notifications
                
                messages_deleted = cleanup_expired_messages()
                notifications_deleted = cleanup_expired_notifications()
                
                if messages_deleted > 0 or notifications_deleted > 0:
                    logger.info(f"Nettoyage automatique: {messages_deleted} messages et {notifications_deleted} notifications supprimés")
                
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage automatique: {e}")
    
    # Démarrer le scheduler de nettoyage automatique
    if not scheduler.running:
        scheduler.add_job(
            func=scheduled_cleanup,
            trigger=IntervalTrigger(hours=1),  # Toutes les heures
            id='cleanup_job',
            name='Nettoyage automatique des messages et notifications',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Scheduler de nettoyage automatique démarré")
    
    logger.info("Application Meet créée avec succès")
    return app


if __name__ == '__main__':
    app = create_app()
    # Configuration de production
    app.run(host='0.0.0.0', port=5001, debug=False)