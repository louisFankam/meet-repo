"""
Middleware de sécurité pour l'application Meet
Applique les headers de sécurité HTTP
"""

from flask import Flask, request, g
import logging

logger = logging.getLogger(__name__)


def apply_security_headers(app: Flask):
    """Applique les headers de sécurité à toutes les réponses"""
    
    @app.after_request
    def add_security_headers(response):
        """Ajoute les headers de sécurité à la réponse HTTP"""
        
        # Headers de base
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Headers HTTPS (si disponible)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Headers de confidentialité
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=(), '
            'accelerometer=(), autoplay=(), encrypted-media=(), '
            'fullscreen=(), picture-in-picture=()'
        )
        
        # Cache control pour les pages sensibles
        if request.endpoint in ['login', 'register', 'profile']:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    logger.info("Middleware de sécurité appliqué")
    return app


def log_request_details():
    """Log les détails des requêtes pour la sécurité"""
    
    # Logger les informations sensibles (sans données confidentielles)
    logger.info(f"Requête: {request.method} {request.path}")
    logger.debug(f"IP: {request.remote_addr}")
    logger.debug(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Détecter des patterns suspects
    suspicious_patterns = [
        '<script', 'javascript:', 'onload=', 'onerror=', 
        '../', '..\\', 'union select', 'drop table',
        'insert into', 'delete from', 'update set'
    ]
    
    request_data = request.get_data(as_text=True) if request.data else ""
    for pattern in suspicious_patterns:
        if pattern.lower() in request_data.lower():
            logger.warning(f"Pattern suspect détecté: {pattern}")
            logger.warning(f"Requête suspecte de {request.remote_addr}")
            break


def security_monitoring():
    """Surveillance de sécurité active"""
    
    # Vérifier les tentatives de force brute
    g.request_start_time = time.time()
    
    # Logger l'IP et le user agent pour détection d'anomalies
    g.client_ip = request.remote_addr
    g.user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Détecter les requêtes anormales
    if len(request.data) > 10 * 1024 * 1024:  # > 10MB
        logger.warning(f"Requête anormalement grande: {len(request.data)} bytes de {g.client_ip}")


import time