
"""
Services métier pour l'application Meet
Logique métier séparée des routes
"""

from .models import User, Message, Like, Match, Notification, Interest, UserInterest
from .database import db
from .extensions import get_timezone_aware_datetime
from datetime import timedelta
from PIL import Image
import os
import logging
from werkzeug.utils import secure_filename
from flask import current_app, has_app_context


class MatchDisplay:
    """Classe simple pour l'affichage des matches dans les templates"""
    def __init__(self, user, last_message, match_date):
        self.user = user
        self.last_message = last_message
        self.match_date = match_date


class ConversationDisplay:
    """Classe simple pour l'affichage des conversations dans les templates"""
    def __init__(self, other_user, last_message, unread_count):
        self.other_user = other_user
        self.last_message = last_message
        self.unread_count = unread_count

logger = logging.getLogger(__name__)


class UserService:
    """Service pour la gestion des utilisateurs"""
    
    @staticmethod
    def create_user(email, password, first_name, last_name, birth_date, gender, interested_in, city, bio=None):
        """Crée un nouvel utilisateur"""
        try:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                gender=gender,
                interested_in=interested_in,
                city=city,
                bio=bio
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.flush()  # Pour obtenir l'ID
            
            logger.info(f"Nouvel utilisateur créé: {user.id}")
            return user
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_user_by_email(email):
        """Récupère un utilisateur par son email"""
        try:
            # S'assurer que nous avons un contexte d'application
            if not has_app_context():
                logger.error("Tentative d'accès à la base de données sans contexte d'application")
                return None
            
            # Debug: Vérifier l'état de la base de données
            from flask import current_app
            logger.debug(f"App context: {current_app}")
            logger.debug(f"Database URI: {current_app.config.get('SQLALCHEMY_DATABASE_URI')}")
            logger.debug(f"Database engine: {db.engine}")
            
            # Debug: Vérifier si le modèle User est correctement lié
            logger.debug(f"User model: {User}")
            logger.debug(f"User query: {User.query}")
            
            # Utiliser une session propre pour cette requête
            result = User.query.filter_by(email=email).first()
            logger.debug(f"Recherche utilisateur par email '{email}': {result}")
            
            # Debug: Vérifier tous les utilisateurs dans la base
            all_users = User.query.all()
            logger.debug(f"Tous les utilisateurs dans la base: {all_users}")
            
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de l'utilisateur par email '{email}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Récupère un utilisateur par son ID"""
        try:
            if not has_app_context():
                logger.error("Tentative d'accès à la base de données sans contexte d'application")
                return None
            
            result = User.query.get(user_id)
            logger.debug(f"Recherche utilisateur par ID '{user_id}': {result}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de l'utilisateur par ID '{user_id}': {e}")
            return None
    
    @staticmethod
    def update_user_profile(user, **kwargs):
        """Met à jour le profil d'un utilisateur"""
        try:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = get_timezone_aware_datetime()
            db.session.commit()
            
            logger.info(f"Profil utilisateur {user.id} mis à jour")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_suggested_users(current_user, min_age=None, max_age=None, city=None, interest=None, limit=20):
        """Récupère les profils suggérés pour un utilisateur"""
        try:
            from datetime import date
            
            # Normaliser les genres pour éviter les problèmes de casse
            interested_gender = current_user.interested_in.lower()
            if interested_gender == 'femmes':
                interested_gender = 'femme'
            elif interested_gender == 'hommes':
                interested_gender = 'homme'
            
            # Construire la requête de base
            query = User.query.filter(
                User.id != current_user.id,
                User.is_active == True,
                db.func.lower(User.gender) == interested_gender
            )
            
            # Appliquer les filtres
            if min_age:
                max_date = date.today() - timedelta(days=min_age*365)
                query = query.filter(User.birth_date <= max_date)
            
            if max_age:
                min_date = date.today() - timedelta(days=max_age*365)
                query = query.filter(User.birth_date >= min_date)
            
            if city:
                query = query.filter(User.city.ilike(f'%{city}%'))
            
            if interest:
                query = query.join(UserInterest).join(Interest).filter(Interest.name == interest)
            
            # Exclure les profils déjà likés
            liked_users = db.session.query(Like.liked_id).filter(Like.liker_id == current_user.id)
            query = query.filter(~User.id.in_(liked_users))
            
            # Limiter les résultats
            return query.limit(limit).all()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des suggestions: {e}")
            return []
    
    @staticmethod
    def save_photo(file, user_id, photo_type):
        """Sauvegarde une photo de profil"""
        try:
            if file and UserService.allowed_file(file.filename):
                # Générer un nom de fichier unique
                filename = f"{user_id}_{photo_type}_{int(get_timezone_aware_datetime().timestamp())}.jpg"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Ouvrir et redimensionner l'image
                image = Image.open(file)
                image = image.convert('RGB')
                
                # Redimensionner si trop grande
                max_size = (800, 800)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Sauvegarder
                image.save(filepath, 'JPEG', quality=85)
                return filename
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la photo: {e}")
            return None
    
    @staticmethod
    def allowed_file(filename):
        """Vérifie si l'extension du fichier est autorisée"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


class LikeService:
    """Service pour la gestion des likes"""
    
    @staticmethod
    def create_like(liker_id, liked_id):
        """Crée un like et vérifie si c'est un match"""
        try:
            # Vérifier si le like existe déjà
            existing_like = Like.query.filter_by(liker_id=liker_id, liked_id=liked_id).first()
            if existing_like:
                return None, False
            
            # Créer le like
            like = Like(liker_id=liker_id, liked_id=liked_id)
            db.session.add(like)
            
            # Vérifier si c'est un match mutuel
            mutual_like = Like.query.filter_by(liker_id=liked_id, liked_id=liker_id).first()
            is_match = False
            
            if mutual_like:
                is_match = True
                # Créer le match
                match = Match(user1_id=min(liker_id, liked_id), user2_id=max(liker_id, liked_id))
                db.session.add(match)
                
                # Créer les notifications
                NotificationService.create_notification(liked_id, f"Vous avez un nouveau match !", 'match')
                NotificationService.create_notification(liker_id, f"Vous avez un nouveau match !", 'match')
            
            db.session.commit()
            
            logger.info(f"Like créé: {liker_id} -> {liked_id}, match: {is_match}")
            return like, is_match
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du like: {e}")
            db.session.rollback()
            return None, False
    
    @staticmethod
    def remove_like(liker_id, liked_id):
        """Supprime un like"""
        try:
            like = Like.query.filter_by(liker_id=liker_id, liked_id=liked_id).first()
            if like:
                db.session.delete(like)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du like: {e}")
            db.session.rollback()
            return False


class MessageService:
    """Service pour la gestion des messages"""
    
    @staticmethod
    def send_message(sender_id, receiver_id, content):
        """Envoie un message"""
        try:
            # Vérifier que c'est un match
            mutual_like = (
                Like.query.filter_by(liker_id=sender_id, liked_id=receiver_id).first() and
                Like.query.filter_by(liker_id=receiver_id, liked_id=sender_id).first()
            )
            
            if not mutual_like:
                return None
            
            # Créer le message
            expires_at = get_timezone_aware_datetime() + timedelta(hours=24)
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                expires_at=expires_at
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Créer une notification
            NotificationService.create_notification(receiver_id, f"Vous avez reçu un nouveau message", 'message')
            
            logger.info(f"Message envoyé: {sender_id} -> {receiver_id}")
            return message
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_conversation(user1_id, user2_id):
        """Récupère la conversation entre deux utilisateurs"""
        try:
            messages = Message.query.filter(
                ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
                ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
            ).order_by(Message.created_at).all()
            
            return messages
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la conversation: {e}")
            return []
    
    @staticmethod
    def get_user_conversations(user_id):
        """Récupère toutes les conversations d'un utilisateur"""
        try:
            # Récupérer les IDs des utilisateurs avec qui l'utilisateur a conversé
            sent = db.session.query(Message.receiver_id).filter(Message.sender_id == user_id)
            received = db.session.query(Message.sender_id).filter(Message.receiver_id == user_id)
            
            conversation_ids = set([id[0] for id in sent.union(received).all()])
            
            conversations = []
            for other_user_id in conversation_ids:
                other_user = User.query.get(other_user_id)
                if other_user:
                    # Récupérer le dernier message
                    last_message = Message.query.filter(
                        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
                        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
                    ).order_by(Message.created_at.desc()).first()
                    
                    conversations.append(ConversationDisplay(other_user, last_message, 0))
            
            # Trier par date du dernier message
            conversations.sort(key=lambda x: x.last_message.created_at if x.last_message else datetime.min, reverse=True)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des conversations: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_messages():
        """Supprime les messages expirés"""
        try:
            now = get_timezone_aware_datetime()
            expired_messages = Message.query.filter(Message.expires_at < now).all()
            
            for message in expired_messages:
                db.session.delete(message)
            
            db.session.commit()
            logger.info(f"Nettoyage de {len(expired_messages)} messages expirés")
            return len(expired_messages)
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des messages: {e}")
            return 0


class MatchService:
    """Service pour la gestion des matches"""
    
    @staticmethod
    def get_user_matches(user_id):
        """Récupère tous les matches d'un utilisateur"""
        try:
            matches = Match.query.filter(
                (Match.user1_id == user_id) | (Match.user2_id == user_id)
            ).all()
            
            matches_data = []
            for match in matches:
                other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
                other_user = User.query.get(other_user_id)
                
                if other_user:
                    # Récupérer le dernier message
                    last_message = Message.query.filter(
                        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
                        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
                    ).order_by(Message.created_at.desc()).first()
                    
                    matches_data.append(MatchDisplay(other_user, last_message, match.created_at))
            
            # Trier par date de match
            matches_data.sort(key=lambda x: x.match_date, reverse=True)
            
            return matches_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des matches: {e}")
            return []
    
    @staticmethod
    def get_received_likes(user_id):
        """Récupère tous les likes reçus par un utilisateur (sans matcher)"""
        try:
            # Récupérer tous les likes reçus
            received_likes = Like.query.filter_by(liked_id=user_id).all()
            
            # Filtrer pour exclure les matches existants
            likes_data = []
            for like in received_likes:
                # Vérifier si un match existe déjà
                existing_match = Match.query.filter(
                    ((Match.user1_id == user_id) & (Match.user2_id == like.liker_id)) |
                    ((Match.user1_id == like.liker_id) & (Match.user2_id == user_id))
                ).first()
                
                if not existing_match:
                    # Pas de match existant, on inclut ce like
                    liker_user = User.query.get(like.liker_id)
                    if liker_user:
                        likes_data.append({
                            'like': like,
                            'user': liker_user
                        })
            
            # Trier par date de like (plus récent en premier)
            likes_data.sort(key=lambda x: x['like'].created_at, reverse=True)
            
            return likes_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des likes reçus: {e}")
            return []
    
    @staticmethod
    def unmatch_users(user1_id, user2_id):
        """Supprime un match entre deux utilisateurs"""
        try:
            # Supprimer les likes mutuels
            Like.query.filter_by(liker_id=user1_id, liked_id=user2_id).delete()
            Like.query.filter_by(liker_id=user2_id, liked_id=user1_id).delete()
            
            # Supprimer le match
            match = Match.query.filter(
                (Match.user1_id == user1_id) & (Match.user2_id == user2_id) |
                (Match.user1_id == user2_id) & (Match.user2_id == user1_id)
            ).first()
            
            if match:
                db.session.delete(match)
            
            # Supprimer tous les messages échangés
            Message.query.filter(
                ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
                ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Match supprimé entre {user1_id} et {user2_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du match: {e}")
            db.session.rollback()
            return False


class NotificationService:
    """Service pour la gestion des notifications"""
    
    @staticmethod
    def create_notification(user_id, message, notification_type):
        """Crée une notification"""
        try:
            expires_at = get_timezone_aware_datetime() + timedelta(hours=24)
            notification = Notification(
                user_id=user_id,
                message=message,
                type=notification_type,
                expires_at=expires_at
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return notification
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification: {e}")
            return None
    
    @staticmethod
    def get_user_notifications(user_id, limit=10):
        """Récupère les notifications d'un utilisateur"""
        try:
            now = get_timezone_aware_datetime()
            notifications = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.expires_at > now
            ).order_by(Notification.created_at.desc()).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_notifications():
        """Supprime les notifications expirées"""
        try:
            now = get_timezone_aware_datetime()
            expired_notifications = Notification.query.filter(Notification.expires_at < now).all()
            
            for notification in expired_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            logger.info(f"Nettoyage de {len(expired_notifications)} notifications expirées")
            return len(expired_notifications)
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des notifications: {e}")
            return 0


class InterestService:
    """Service pour la gestion des centres d'intérêt"""
    
    @staticmethod
    def get_all_interests():
        """Récupère tous les centres d'intérêt"""
        return Interest.query.all()
    
    @staticmethod
    def get_interest_by_name(name):
        """Récupère un centre d'intérêt par son nom"""
        return Interest.query.filter_by(name=name).first()
    
    @staticmethod
    def create_interest(name, category=None):
        """Crée un nouveau centre d'intérêt"""
        try:
            interest = Interest(name=name, category=category)
            db.session.add(interest)
            db.session.commit()
            return interest
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du centre d'intérêt: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def add_user_interest(user_id, interest_id):
        """Ajoute un centre d'intérêt à un utilisateur"""
        try:
            # Vérifier si l'association existe déjà
            existing = UserInterest.query.filter_by(user_id=user_id, interest_id=interest_id).first()
            if existing:
                return False
            
            user_interest = UserInterest(user_id=user_id, interest_id=interest_id)
            db.session.add(user_interest)
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du centre d'intérêt: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def remove_user_interest(user_id, interest_id):
        """Supprime un centre d'intérêt d'un utilisateur"""
        try:
            user_interest = UserInterest.query.filter_by(user_id=user_id, interest_id=interest_id).first()
            if user_interest:
                db.session.delete(user_interest)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du centre d'intérêt: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def initialize_default_interests():
        """Initialise les centres d'intérêt par défaut"""
        default_interests = [
            ('Sport', 'Activités physiques'),
            ('Musique', 'Arts'),
            ('Voyage', 'Découverte'),
            ('Cuisine', 'Gastronomie'),
            ('Art', 'Créativité'),
            ('Lecture', 'Culture'),
            ('Cinéma', 'Divertissement'),
            ('Nature', 'Environnement'),
            ('Technologie', 'Innovation'),
            ('Mode', 'Style'),
            ('Photographie', 'Créativité'),
            ('Danse', 'Arts'),
            ('Théâtre', 'Arts'),
            ('Jeux vidéo', 'Divertissement'),
            ('Yoga', 'Bien-être'),
            ('Méditation', 'Bien-être')
        ]
        
        try:
            for name, category in default_interests:
                if not Interest.query.filter_by(name=name).first():
                    interest = Interest(name=name, category=category)
                    db.session.add(interest)
            
            db.session.commit()
            logger.info("Centres d'intérêt par défaut initialisés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des centres d'intérêt: {e}")
            db.session.rollback()