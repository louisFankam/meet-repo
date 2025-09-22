#!/usr/bin/env python3
"""
Script de nettoyage des likes orphelins
Supprime les likes qui ont déjà été transformés en matches
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app()
from model.database import db
from model.models import Like, Match
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_orphaned_likes():
    """Nettoie les likes orphelins (likes qui ont déjà été transformés en matches)"""
    try:
        with app.app_context():
            # Récupérer tous les matches
            matches = Match.query.all()
            logger.info(f"Trouvé {len(matches)} matches à vérifier")
            
            deleted_count = 0
            
            for match in matches:
                # Vérifier s'il existe des likes entre ces deux utilisateurs
                likes_between_users = Like.query.filter(
                    ((Like.liker_id == match.user1_id) & (Like.liked_id == match.user2_id)) |
                    ((Like.liker_id == match.user2_id) & (Like.liked_id == match.user1_id))
                ).all()
                
                if likes_between_users:
                    logger.info(f"Suppression de {len(likes_between_users)} likes orphelins pour le match {match.user1_id} <-> {match.user2_id}")
                    
                    for like in likes_between_users:
                        db.session.delete(like)
                        deleted_count += 1
            
            if deleted_count > 0:
                db.session.commit()
                logger.info(f"Nettoyage terminé : {deleted_count} likes orphelins supprimés")
            else:
                logger.info("Aucun like orphelin trouvé")
                
            return deleted_count
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage : {e}")
        db.session.rollback()
        return 0

def show_stats():
    """Affiche des statistiques sur les likes et matches"""
    try:
        with app.app_context():
            total_likes = Like.query.count()
            total_matches = Match.query.count()
            
            logger.info(f"Statistiques actuelles :")
            logger.info(f"- Total likes : {total_likes}")
            logger.info(f"- Total matches : {total_matches}")
            
            # Compter les likes orphelins
            orphaned_count = 0
            matches = Match.query.all()
            
            for match in matches:
                likes_between_users = Like.query.filter(
                    ((Like.liker_id == match.user1_id) & (Like.liked_id == match.user2_id)) |
                    ((Like.liker_id == match.user2_id) & (Like.liked_id == match.user1_id))
                ).count()
                orphaned_count += likes_between_users
            
            logger.info(f"- Likes orphelins détectés : {orphaned_count}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des statistiques : {e}")

if __name__ == "__main__":
    logger.info("Début du nettoyage des likes orphelins...")
    
    # Afficher les statistiques avant
    show_stats()
    
    # Effectuer le nettoyage
    deleted = cleanup_orphaned_likes()
    
    # Afficher les statistiques après
    show_stats()
    
    if deleted > 0:
        logger.info("✅ Nettoyage réussi !")
    else:
        logger.info("✅ Aucun nettoyage nécessaire")