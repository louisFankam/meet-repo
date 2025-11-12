"""
Module de logging de sécurité pour la détection d'intrusions
Enregistre les activités suspectes et les tentatives d'attaque
"""

import logging
import json
from datetime import datetime
from flask import request
from typing import Dict, Any, Optional
import hashlib


class SecurityLogger:
    """Logger spécialisé pour la sécurité et la détection d'intrusions"""
    
    def __init__(self):
        # Créer le dossier logs s'il n'existe pas
        import os
        os.makedirs('logs', exist_ok=True)
        
        # Créer un logger dédié à la sécurité
        self.logger = logging.getLogger('security')
        
        # Configurer le handler pour les logs de sécurité
        if not self.logger.handlers:
            handler = logging.FileHandler('logs/security.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_client_info(self) -> Dict[str, str]:
        """Récupère les informations sur le client"""
        return {
            'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'method': request.method,
            'endpoint': request.endpoint,
            'url': request.url,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _create_fingerprint(self, data: Dict[str, Any]) -> str:
        """Crée une empreinte pour identifier les attaques récurrentes"""
        fingerprint_data = f"{data.get('ip')}_{data.get('user_agent')}_{data.get('endpoint')}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]
    
    def log_sql_injection_attempt(self, input_data: str, field_name: str):
        """Log une tentative d'injection SQL"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'SQL_INJECTION_ATTEMPT',
            'severity': 'HIGH',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'field': field_name,
                'input_length': len(input_data),
                'input_preview': input_data[:100] + '...' if len(input_data) > 100 else input_data
            }
        }
        
        self.logger.warning(f"SQL_INJECTION_ATTEMPT: {json.dumps(security_event)}")
    
    def log_xss_attempt(self, input_data: str, field_name: str):
        """Log une tentative d'attaque XSS"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'XSS_ATTEMPT',
            'severity': 'HIGH',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'field': field_name,
                'input_length': len(input_data),
                'input_preview': input_data[:100] + '...' if len(input_data) > 100 else input_data
            }
        }
        
        self.logger.warning(f"XSS_ATTEMPT: {json.dumps(security_event)}")
    
    def log_brute_force_attempt(self, email: str, reason: str):
        """Log une tentative de force brute"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'BRUTE_FORCE_ATTEMPT',
            'severity': 'MEDIUM',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'email': email,
                'reason': reason
            }
        }
        
        self.logger.warning(f"BRUTE_FORCE_ATTEMPT: {json.dumps(security_event)}")
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log une activité suspecte générique"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': activity_type,
            'severity': 'MEDIUM',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': details
        }
        
        self.logger.warning(f"SUSPICIOUS_ACTIVITY: {json.dumps(security_event)}")
    
    def log_invalid_input(self, field_name: str, input_data: str, validation_errors: list):
        """Log une entrée invalide qui pourrait être une tentative d'attaque"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        # Vérifier si les erreurs de validation suggèrent une attaque
        is_potential_attack = any([
            'injection' in error.lower() for error in validation_errors
        ] or [
            'xss' in error.lower() for error in validation_errors
        ] or [
            'forbidden' in error.lower() for error in validation_errors
        ])
        
        severity = 'HIGH' if is_potential_attack else 'LOW'
        
        security_event = {
            'type': 'INVALID_INPUT',
            'severity': severity,
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'field': field_name,
                'input_length': len(input_data),
                'validation_errors': validation_errors,
                'potential_attack': is_potential_attack
            }
        }
        
        if is_potential_attack:
            self.logger.warning(f"INVALID_INPUT: {json.dumps(security_event)}")
        else:
            self.logger.info(f"INVALID_INPUT: {json.dumps(security_event)}")
    
    def log_rate_limit_violation(self, limit_type: str):
        """Log une violation de rate limiting"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'RATE_LIMIT_VIOLATION',
            'severity': 'MEDIUM',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'limit_type': limit_type
            }
        }
        
        self.logger.warning(f"RATE_LIMIT_VIOLATION: {json.dumps(security_event)}")
    
    def log_unauthorized_access_attempt(self, resource: str, user_id: Optional[int] = None):
        """Log une tentative d'accès non autorisée"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'UNAUTHORIZED_ACCESS',
            'severity': 'HIGH',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'resource': resource,
                'user_id': user_id
            }
        }
        
        self.logger.warning(f"UNAUTHORIZED_ACCESS: {json.dumps(security_event)}")
    
    def log_file_upload_attempt(self, filename: str, file_type: str, file_size: int):
        """Log une tentative d'upload de fichier"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'FILE_UPLOAD',
            'severity': 'LOW',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size
            }
        }
        
        self.logger.info(f"FILE_UPLOAD: {json.dumps(security_event)}")
    
    def log_admin_access_attempt(self, success: bool, email: str):
        """Log une tentative d'accès admin"""
        client_info = self._get_client_info()
        fingerprint = self._create_fingerprint(client_info)
        
        security_event = {
            'type': 'ADMIN_ACCESS_ATTEMPT',
            'severity': 'HIGH' if not success else 'INFO',
            'fingerprint': fingerprint,
            'client': client_info,
            'details': {
                'email': email,
                'success': success
            }
        }
        
        if success:
            self.logger.info(f"ADMIN_ACCESS_ATTEMPT: {json.dumps(security_event)}")
        else:
            self.logger.warning(f"ADMIN_ACCESS_ATTEMPT: {json.dumps(security_event)}")
    
    def get_recent_intrusion_attempts(self, minutes: int = 60) -> Dict[str, int]:
        """Analyse les logs pour détecter des tentatives d'intrusion récentes"""
        # Cette fonction pourrait être implémentée pour analyser les logs de sécurité
        # et retourner des statistiques sur les tentatives d'intrusion
        return {
            'sql_injection': 0,
            'xss': 0,
            'brute_force': 0,
            'rate_limit_violations': 0,
            'unauthorized_access': 0
        }


# Instance globale
security_logger = SecurityLogger()