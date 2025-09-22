"""
Base de données pour l'application Meet
Configuration centralisée de la base de données
"""

from .extensions import db

# Exporter la base de données pour l'utiliser dans les modèles
__all__ = ['db']