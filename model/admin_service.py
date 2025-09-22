"""
Service d'administration pour la gestion complète de l'application
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from .database import db
from .models import User, Message, Like, Match, Notification, Interest, UserInterest
from .extensions import get_timezone_aware_datetime

logger = logging.getLogger(__name__)

class AdminService:
    """Service central pour toutes les opérations d'administration"""
    
    @staticmethod
    def get_dashboard_stats():
        """Récupère les statistiques générales du dashboard"""
        try:
            # Statistiques de base
            total_users = User.query.count()
            active_users = User.query.filter(User.is_active == True).count()
            total_matches = Match.query.count()
            total_messages = Message.query.count()
            total_likes = Like.query.count()
            
            # Utilisateurs récents (7 derniers jours)
            week_ago = get_timezone_aware_datetime() - timedelta(days=7)
            recent_users = User.query.filter(User.created_at >= week_ago).count()
            
            # Messages récents (24h)
            day_ago = get_timezone_aware_datetime() - timedelta(days=1)
            recent_messages = Message.query.filter(Message.created_at >= day_ago).count()
            
            # Matches récents (7 jours)
            recent_matches = Match.query.filter(Match.created_at >= week_ago).count()
            
            # Conversations actives (utilisateurs avec messages des dernières 24h)
            active_conversations = db.session.query(Message.sender_id).filter(
                Message.created_at >= day_ago
            ).union(
                db.session.query(Message.receiver_id).filter(
                    Message.created_at >= day_ago
                )
            ).distinct().count()
            
            # Taux d'activité
            activity_rate = (active_users / total_users * 100) if total_users > 0 else 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_matches': total_matches,
                'total_messages': total_messages,
                'total_likes': total_likes,
                'recent_users': recent_users,
                'recent_messages': recent_messages,
                'recent_matches': recent_matches,
                'active_conversations': active_conversations,
                'activity_rate': round(activity_rate, 1)
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {}
    
    @staticmethod
    def get_recent_users(limit=10):
        """Récupère les utilisateurs récents"""
        try:
            return User.query.order_by(desc(User.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs récents: {e}")
            return []
    
    @staticmethod
    def get_recent_messages(limit=10):
        """Récupère les messages récents"""
        try:
            return Message.query.order_by(desc(Message.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des messages récents: {e}")
            return []
    
    @staticmethod
    def get_all_users(page=1, per_page=20, search=None, filter_status=None):
        """Récupère tous les utilisateurs avec pagination et filtres"""
        try:
            query = User.query
            
            # Filtre de recherche
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        User.email.ilike(search_term),
                        User.city.ilike(search_term)
                    )
                )
            
            # Filtre par statut
            if filter_status == 'active':
                query = query.filter(User.is_active == True)
            elif filter_status == 'inactive':
                query = query.filter(User.is_active == False)
            
            # Pagination
            users = query.order_by(desc(User.created_at)).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return users
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            return None
    
    @staticmethod
    def get_user_details(user_id):
        """Récupère les détails complets d'un utilisateur"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Statistiques de l'utilisateur
            stats = {
                'likes_sent': Like.query.filter_by(liker_id=user_id).count(),
                'likes_received': Like.query.filter_by(liked_id=user_id).count(),
                'matches': Match.query.filter(
                    or_(Match.user1_id == user_id, Match.user2_id == user_id)
                ).count(),
                'messages_sent': Message.query.filter_by(sender_id=user_id).count(),
                'messages_received': Message.query.filter_by(receiver_id=user_id).count(),
                'interests_count': UserInterest.query.filter_by(user_id=user_id).count()
            }
            
            return {
                'user': user,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails utilisateur: {e}")
            return None
    
    @staticmethod
    def toggle_user_status(user_id):
        """Active/désactive un utilisateur"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Utilisateur non trouvé"
            
            user.is_active = not user.is_active
            db.session.commit()
            
            status = "activé" if user.is_active else "désactivé"
            return True, f"Utilisateur {status} avec succès"
        except Exception as e:
            logger.error(f"Erreur lors du changement de statut utilisateur: {e}")
            db.session.rollback()
            return False, "Erreur lors du changement de statut"
    
    @staticmethod
    def delete_user(user_id):
        """Supprime un utilisateur et toutes ses données"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Utilisateur non trouvé"
            
            # Supprimer les données associées
            Like.query.filter(
                or_(Like.liker_id == user_id, Like.liked_id == user_id)
            ).delete()
            
            Match.query.filter(
                or_(Match.user1_id == user_id, Match.user2_id == user_id)
            ).delete()
            
            Message.query.filter(
                or_(Message.sender_id == user_id, Message.receiver_id == user_id)
            ).delete()
            
            Notification.query.filter_by(user_id=user_id).delete()
            UserInterest.query.filter_by(user_id=user_id).delete()
            
            # Supprimer l'utilisateur
            db.session.delete(user)
            db.session.commit()
            
            return True, "Utilisateur supprimé avec succès"
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            db.session.rollback()
            return False, "Erreur lors de la suppression"
    
    @staticmethod
    def get_system_logs(level='INFO', limit=100):
        """Récupère les logs système"""
        # Cette fonction nécessiterait une configuration de logging avancée
        # Pour l'instant, retourne une structure vide
        return {
            'logs': [],
            'total': 0
        }
    
    @staticmethod
    def cleanup_expired_data():
        """Nettoie les données expirées"""
        try:
            now = get_timezone_aware_datetime()
            
            # Nettoyer les messages expirés
            expired_messages = Message.query.filter(Message.expires_at < now).delete()
            
            # Nettoyer les notifications expirées
            expired_notifications = Notification.query.filter(
                Notification.expires_at < now
            ).delete()
            
            # Nettoyer les likes orphelins (plus de 30 jours)
            month_ago = now - timedelta(days=30)
            old_likes = Like.query.filter(Like.created_at < month_ago).delete()
            
            db.session.commit()
            
            return {
                'success': True,
                'expired_messages': expired_messages,
                'expired_notifications': expired_notifications,
                'old_likes': old_likes,
                'total_cleaned': expired_messages + expired_notifications + old_likes
            }
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des données: {e}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_activity_stats(days=30):
        """Récupère les statistiques d'activité sur une période"""
        try:
            start_date = get_timezone_aware_datetime() - timedelta(days=days)
            
            # Nouveaux utilisateurs par jour
            daily_users = db.session.query(
                func.date(User.created_at),
                func.count(User.id)
            ).filter(User.created_at >= start_date).group_by(
                func.date(User.created_at)
            ).all()
            
            # Messages par jour
            daily_messages = db.session.query(
                func.date(Message.created_at),
                func.count(Message.id)
            ).filter(Message.created_at >= start_date).group_by(
                func.date(Message.created_at)
            ).all()
            
            # Matches par jour
            daily_matches = db.session.query(
                func.date(Match.created_at),
                func.count(Match.id)
            ).filter(Match.created_at >= start_date).group_by(
                func.date(Match.created_at)
            ).all()
            
            # Likes par jour
            daily_likes = db.session.query(
                func.date(Like.created_at),
                func.count(Like.id)
            ).filter(Like.created_at >= start_date).group_by(
                func.date(Like.created_at)
            ).all()
            
            return {
                'daily_users': dict(daily_users),
                'daily_messages': dict(daily_messages),
                'daily_matches': dict(daily_matches),
                'daily_likes': dict(daily_likes),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats d'activité: {e}")
            return {}
    
    @staticmethod
    def get_top_users(metric='matches', limit=10):
        """Récupère les top utilisateurs selon différentes métriques"""
        try:
            if metric == 'matches':
                # Utilisateurs avec le plus de matches
                query = db.session.query(
                    User,
                    func.count(Match.id).label('count')
                ).outerjoin(
                    Match,
                    or_(Match.user1_id == User.id, Match.user2_id == User.id)
                ).group_by(User.id).order_by(desc('count')).limit(limit)
                
            elif metric == 'likes_received':
                # Utilisateurs avec le plus de likes reçus
                query = db.session.query(
                    User,
                    func.count(Like.id).label('count')
                ).outerjoin(
                    Like,
                    Like.liked_id == User.id
                ).group_by(User.id).order_by(desc('count')).limit(limit)
                
            elif metric == 'messages_sent':
                # Utilisateurs avec le plus de messages envoyés
                query = db.session.query(
                    User,
                    func.count(Message.id).label('count')
                ).outerjoin(
                    Message,
                    Message.sender_id == User.id
                ).group_by(User.id).order_by(desc('count')).limit(limit)
                
            else:
                return []
            
            return query.all()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des top utilisateurs: {e}")
            return []
    
    @staticmethod
    def export_data(format='json'):
        """Exporte toutes les données de l'application"""
        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'users': [],
                'matches': [],
                'messages': [],
                'likes': [],
                'interests': []
            }
            
            # Exporter les utilisateurs
            for user in User.query.all():
                data['users'].append({
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'age': user.age,
                    'city': user.city,
                    'gender': user.gender,
                    'interested_in': user.interested_in,
                    'bio': user.bio,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                })
            
            # Exporter les matches
            for match in Match.query.all():
                data['matches'].append({
                    'id': match.id,
                    'user1_id': match.user1_id,
                    'user2_id': match.user2_id,
                    'created_at': match.created_at.isoformat()
                })
            
            # Exporter les messages
            for message in Message.query.all():
                data['messages'].append({
                    'id': message.id,
                    'sender_id': message.sender_id,
                    'receiver_id': message.receiver_id,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'expires_at': message.expires_at.isoformat() if message.expires_at else None
                })
            
            # Exporter les likes
            for like in Like.query.all():
                data['likes'].append({
                    'id': like.id,
                    'liker_id': like.liker_id,
                    'liked_id': like.liked_id,
                    'created_at': like.created_at.isoformat()
                })
            
            # Exporter les intérêts
            for interest in Interest.query.all():
                data['interests'].append({
                    'id': interest.id,
                    'name': interest.name,
                    'description': interest.description
                })
            
            return data
        except Exception as e:
            logger.error(f"Erreur lors de l'export des données: {e}")
            return None