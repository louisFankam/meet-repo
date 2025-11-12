"""
Module de validation sécurisée des entrées utilisateur
Protection contre XSS, SQL Injection et injections diverses
"""

import re
import html
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Classe de validation sécurisée pour les entrées utilisateur"""
    
    # Patterns de validation
    PATTERNS = {
        'name': r'^[a-zA-ZÀ-ÿ\s\-\'\.]{1,50}$',  # Noms avec accents
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'city': r'^[a-zA-ZÀ-ÿ\s\-\'\.]{1,100}$',
        'bio': r'^[a-zA-ZÀ-ÿ0-9\s\-\.\,\'!?\*()%&@#]{0,500}$',
        'user_id': r'^[0-9]+$',
        'message': r'^[a-zA-ZÀ-ÿ0-9\s\-\.\,\'!?\*()%&@#éèêëàâäîïôöùûüÿç]{1,1000}$'
    }
    
    # Listes noires
    FORBIDDEN_PATTERNS = [
        r'<script.*?>.*?</script>',  # XSS
        r'javascript:',              # JS URLs
        r'on\w+\s*=',               # Event handlers
        r'select.*?from',            # SQL Injection
        r'drop\s+table',            # SQL Injection
        r'insert\s+into',           # SQL Injection
        r'update.*?set',            # SQL Injection
        r'delete\s+from',           # SQL Injection
        r'union.*?select',          # SQL Injection
        r'exec\s*\(',               # Command execution
        r'system\s*\(',             # Command execution
        r'\$\{.*?\}',               # Template injection
    ]
    
    @classmethod
    def sanitize_string(cls, input_string: str, max_length: int = 1000) -> str:
        """Nettoie une chaîne de caractères"""
        if not isinstance(input_string, str):
            return str(input_string) if input_string else ""
        
        # Limiter la longueur
        input_string = input_string[:max_length]
        
        # Échapper les caractères HTML
        sanitized = html.escape(input_string)
        
        # Supprimer les caractères de contrôle
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    @classmethod
    def validate_pattern(cls, input_string: str, pattern_name: str) -> bool:
        """Valide une chaîne contre un pattern"""
        if pattern_name not in cls.PATTERNS:
            return False
        
        pattern = cls.PATTERNS[pattern_name]
        return bool(re.match(pattern, input_string, re.IGNORECASE | re.UNICODE))
    
    @classmethod
    def contains_forbidden_content(cls, input_string: str) -> List[str]:
        """Détecte du contenu interdit dans une chaîne"""
        threats = []
        input_lower = input_string.lower()
        
        for forbidden_pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(forbidden_pattern, input_lower, re.IGNORECASE):
                threats.append(f"Pattern détecté: {forbidden_pattern}")
        
        return threats
    
    @classmethod
    def validate_name(cls, name: str, field_name: str = "nom") -> Dict[str, Any]:
        """Valide un nom (prénom/nom)"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        if not isinstance(name, str):
            result['errors'].append(f"{field_name} doit être une chaîne de caractères")
            return result
        
        sanitized = cls.sanitize_string(name, 50)
        
        if not sanitized:
            result['errors'].append(f"{field_name} ne peut pas être vide")
            return result
        
        if not cls.validate_pattern(sanitized, 'name'):
            result['errors'].append(f"{field_name} contient des caractères invalides")
            return result
        
        # Vérifier les menaces
        threats = cls.contains_forbidden_content(sanitized)
        if threats:
            result['errors'].append(f"{field_name} contient du contenu non autorisé")
            
            # Logging de sécurité détaillé
            for threat in threats:
                if 'SQL' in threat or 'select' in threat.lower():
                    try:
                        from security_logging import security_logger
                        security_logger.log_sql_injection_attempt(name, field_name)
                    except ImportError:
                        logger.warning(f"Module security_logging non disponible: {threat}")
                elif 'script' in threat.lower() or 'javascript' in threat.lower():
                    try:
                        from security_logging import security_logger
                        security_logger.log_xss_attempt(name, field_name)
                    except ImportError:
                        logger.warning(f"Module security_logging non disponible: {threat}")
            
            logger.warning(f"Tentative d'injection détectée dans {field_name}: {threats}")
            return result
        
        result['valid'] = True
        result['sanitized'] = sanitized
        return result
    
    @classmethod
    def validate_email(cls, email: str) -> Dict[str, Any]:
        """Valide un email de manière sécurisée"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        if not isinstance(email, str):
            result['errors'].append("Email doit être une chaîne de caractères")
            return result
        
        sanitized = cls.sanitize_string(email.lower(), 100)
        
        if not sanitized:
            result['errors'].append("Email ne peut pas être vide")
            return result
        
        if not cls.validate_pattern(sanitized, 'email'):
            result['errors'].append("Format d'email invalide")
            return result
        
        # Vérifications supplémentaires
        if sanitized.count('@') != 1:
            result['errors'].append("Email doit contenir exactement un @")
            return result
        
        local, domain = sanitized.split('@')
        
        if len(local) < 1 or len(local) > 64:
            result['errors'].append("Partie locale de l'email invalide")
            return result
        
        if len(domain) < 4 or len(domain) > 253:
            result['errors'].append("Domaine de l'email invalide")
            return result
        
        result['valid'] = True
        result['sanitized'] = sanitized
        return result
    
    @classmethod
    def validate_city(cls, city: str) -> Dict[str, Any]:
        """Valide un nom de ville"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        if not isinstance(city, str):
            result['errors'].append("Ville doit être une chaîne de caractères")
            return result
        
        sanitized = cls.sanitize_string(city, 100)
        
        if not sanitized:
            result['errors'].append("Ville ne peut pas être vide")
            return result
        
        if not cls.validate_pattern(sanitized, 'city'):
            result['errors'].append("Ville contient des caractères invalides")
            return result
        
        threats = cls.contains_forbidden_content(sanitized)
        if threats:
            result['errors'].append("Ville contient du contenu non autorisé")
            logger.warning(f"Tentative d'injection détectée dans ville: {threats}")
            return result
        
        result['valid'] = True
        result['sanitized'] = sanitized
        return result
    
    @classmethod
    def validate_bio(cls, bio: str) -> Dict[str, Any]:
        """Valide une bio/description"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        if not isinstance(bio, str):
            result['errors'].append("Bio doit être une chaîne de caractères")
            return result
        
        sanitized = cls.sanitize_string(bio, 500)
        
        # La bio peut être vide
        if not sanitized:
            result['valid'] = True
            result['sanitized'] = ""
            return result
        
        if not cls.validate_pattern(sanitized, 'bio'):
            result['errors'].append("Bio contient des caractères invalides")
            return result
        
        threats = cls.contains_forbidden_content(sanitized)
        if threats:
            result['errors'].append("Bio contient du contenu non autorisé")
            logger.warning(f"Tentative d'injection détectée dans bio: {threats}")
            return result
        
        result['valid'] = True
        result['sanitized'] = sanitized
        return result
    
    @classmethod
    def validate_message(cls, message: str) -> Dict[str, Any]:
        """Valide un message"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        if not isinstance(message, str):
            result['errors'].append("Message doit être une chaîne de caractères")
            return result
        
        sanitized = cls.sanitize_string(message, 1000)
        
        if not sanitized.strip():
            result['errors'].append("Message ne peut pas être vide")
            return result
        
        if not cls.validate_pattern(sanitized, 'message'):
            result['errors'].append("Message contient des caractères invalides")
            return result
        
        threats = cls.contains_forbidden_content(sanitized)
        if threats:
            result['errors'].append("Message contient du contenu non autorisé")
            logger.warning(f"Tentative d'injection détectée dans message: {threats}")
            return result
        
        result['valid'] = True
        result['sanitized'] = sanitized
        return result
    
    @classmethod
    def validate_user_id(cls, user_id: Any) -> Dict[str, Any]:
        """Valide un ID utilisateur"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        try:
            # Convertir en string pour validation
            user_id_str = str(user_id)
            
            if not user_id_str.isdigit():
                result['errors'].append("ID utilisateur doit être numérique")
                return result
            
            # Vérifier la plage raisonnable
            user_id_int = int(user_id_str)
            if user_id_int < 1 or user_id_int > 999999999:
                result['errors'].append("ID utilisateur hors plage valide")
                return result
            
            result['valid'] = True
            result['sanitized'] = user_id_int
            return result
            
        except (ValueError, TypeError):
            result['errors'].append("ID utilisateur invalide")
            return result
    
    @classmethod
    def validate_date(cls, date_string: str, min_age: int = 18, max_age: int = 120) -> Dict[str, Any]:
        """Valide une date de naissance"""
        result = {'valid': False, 'sanitized': None, 'errors': []}
        
        if not isinstance(date_string, str):
            result['errors'].append("Date doit être une chaîne de caractères")
            return result
        
        try:
            # Parser la date
            parsed_date = datetime.strptime(date_string, '%Y-%m-%d').date()
            
            # Calculer l'âge
            today = date.today()
            age = today.year - parsed_date.year - ((today.month, today.day) < (parsed_date.month, parsed_date.day))
            
            if age < min_age:
                result['errors'].append(f"Vous devez avoir au moins {min_age} ans")
                return result
            
            if age > max_age:
                result['errors'].append(f"Âge maximum autorisé: {max_age} ans")
                return result
            
            # Vérifier que la date n'est pas dans le futur
            if parsed_date > today:
                result['errors'].append("La date ne peut pas être dans le futur")
                return result
            
            result['valid'] = True
            result['sanitized'] = parsed_date
            return result
            
        except ValueError:
            result['errors'].append("Format de date invalide (attendu: YYYY-MM-DD)")
            return result


# Instance globale pour faciliter l'utilisation
validator = SecurityValidator()