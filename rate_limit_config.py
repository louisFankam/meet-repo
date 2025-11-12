"""
Configuration de sécurité avancée pour le rate limiting
Définit les limites par type de route et fonctionnalités
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

# Configuration des limites de requêtes
RATE_LIMITS = {
    # Routes publiques - limites strictes
    'register': '5 per minute, 20 per hour',      # Inscription : 5/min, 20/heure
    'login': '10 per minute, 50 per hour',       # Connexion : 10/min, 50/heure
    'password_reset': '3 per minute, 10 per hour', # Reset mot de passe : 3/min, 10/heure
    
    # Routes API - limites modérées
    'api_like': '30 per minute, 200 per hour',   # Like : 30/min, 200/heure
    'api_message': '20 per minute, 100 per hour', # Messages : 20/min, 100/heure
    'api_upload': '10 per minute, 50 per hour',  # Upload : 10/min, 50/heure
    'api_search': '60 per minute, 500 per hour', # Recherche : 60/min, 500/heure
    
    # Routes admin - protection renforcée
    'admin_login': '3 per minute, 10 per hour',   # Login admin : 3/min, 10/heure
    'admin_api': '20 per minute, 200 per hour',   # API admin : 20/min, 200/heure
    
    # Routes générales
    'default': '100 per minute, 1000 per hour'   # Routes normales : 100/min, 1000/heure
}

# Configuration du rate limiter
def configure_rate_limiter(app):
    """Configure le rate limiter avec des paramètres sécurisés"""
    
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=RATE_LIMITS['default'],
        storage_uri="memory://",  # Stockage en mémoire pour le développement
        # Pour la production, utiliser Redis: "redis://localhost:6379"
    )
    
    # Logging des violations de rate limiting
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handler personnalisé pour les violations de rate limiting"""
        logger.warning(f"Rate limit dépassé pour {get_remote_address()} sur {request.endpoint}")
        return {
            'success': False,
            'error': 'Trop de requêtes. Veuillez réessayer plus tard.',
            'message': str(e.description)
        }, 429
    
    logger.info("Rate limiter configuré avec sécurité renforcée")
    return limiter


# Décorateurs de rate limiting personnalisés
def strict_rate_limit(limit_string):
    """Rate limit strict avec logging"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = get_remote_address()
            endpoint = f.__name__
            logger.info(f"Requête rate-limited: {endpoint} depuis {ip}")
            return limiter.limit(limit_string)(f)(*args, **kwargs)
        
        return decorated_function
    return decorator


def critical_rate_limit(limit_string):
    """Rate limit pour routes critiques avec logging avancé"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = get_remote_address()
            endpoint = f.__name__
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            logger.warning(f"Requête critique: {endpoint} depuis {ip} - {user_agent}")
            return limiter.limit(limit_string)(f)(*args, **kwargs)
        
        return decorated_function
    return decorator


# Création du limiter global
limiter = None