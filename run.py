#!/usr/bin/env python3
"""
Contrôleur principal pour l'application Meet
Point d'entrée avec configuration MVC
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire courant au chemin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from model.extensions import logger

# Configuration du logging
def setup_logging():
    """Configure le logging pour l'application"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('meet.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger.info("Logging configuré")


def main():
    """Fonction principale pour démarrer l'application"""
    try:
        setup_logging()
        logger.info("Démarrage de l'application Meet")
        
        # Créer l'application
        app = create_app()
        
        # Configuration du port
        port = int(os.getenv('PORT', 5001))
        
        logger.info(f"Application démarrée sur le port {port}")
        logger.info(f"Environnement: development")
        
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()