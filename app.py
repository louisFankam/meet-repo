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
from security_middleware import apply_security_headers

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
            # Utilisation des variables d'environnement centralisées
            user = os.getenv('DB_USER', 'root')
            password = os.getenv('DB_PASSWORD', '')
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '3306')
            name = os.getenv('DB_NAME', 'meet_db')
            uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        app.config['SQLALCHEMY_DATABASE_URI'] = uri
        
        # Configuration BDD additionnelle
        app.config['DB_USER'] = os.getenv('DB_USER', 'root')
        app.config['DB_PASSWORD'] = os.getenv('DB_PASSWORD', '')
        app.config['DB_HOST'] = os.getenv('DB_HOST', 'localhost')
        app.config['DB_PORT'] = os.getenv('DB_PORT', '3306')
        app.config['DB_NAME'] = os.getenv('DB_NAME', 'meet_db')

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = 'static/uploads'
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
        
        # Configuration production
        is_production = os.getenv('FLASK_ENV') == 'production'
        if is_production:
            app.config['DEBUG'] = False
            app.config['TESTING'] = False
            # Logging en production
            if not app.debug:
                import logging
                from logging.handlers import RotatingFileHandler
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = RotatingFileHandler('logs/meet.log', maxBytes=10240, backupCount=10)
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
                app.logger.setLevel(logging.INFO)
                app.logger.info('Meet startup')
    
    # Initialiser les extensions
    init_extensions(app)
    
    # Appliquer les middlewares de sécurité
    apply_security_headers(app)
    
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
    
    # Configuration du port avec fallback
    port = int(os.getenv('PORT', 5000))
    if port == 5001:
        # Essayer le port 5000 si 5001 est occupé
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 5000))
                port = 5000
        except OSError:
            # Si les deux sont occupés, utiliser 5002
            port = 5002
    
    # Configuration de production
    app.run(host='0.0.0.0', port=port, debug=False)