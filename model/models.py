"""
Modèles de base de données pour l'application Meet
Relations entre les différentes entités
"""

from .database import db
from .extensions import get_timezone_aware_datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class User(UserMixin, db.Model):
    """Modèle Utilisateur"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.Date, nullable=False, index=True)
    gender = db.Column(db.String(20), nullable=False, index=True)
    interested_in = db.Column(db.String(20), nullable=False, index=True)
    city = db.Column(db.String(100), nullable=False, index=True)
    bio = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    second_photo = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_timezone_aware_datetime, index=True)
    last_active = db.Column(db.DateTime, default=get_timezone_aware_datetime, index=True)
    updated_at = db.Column(db.DateTime, default=get_timezone_aware_datetime, onupdate=get_timezone_aware_datetime)
    
    # Relations restaurées pour le fonctionnement de l'application
    user_interests = db.relationship('UserInterest', backref='user', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    likes_given = db.relationship('Like', foreign_keys='Like.liker_id', backref='liker', lazy='dynamic')
    likes_received = db.relationship('Like', foreign_keys='Like.liked_id', backref='liked', lazy='dynamic')
    matches_as_user1 = db.relationship('Match', foreign_keys='Match.user1_id', backref='user1', lazy='dynamic')
    matches_as_user2 = db.relationship('Match', foreign_keys='Match.user2_id', backref='user2', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    # Indexes pour optimiser les performances
    __table_args__ = (
        db.Index('idx_user_search', 'city', 'gender', 'interested_in'),
        db.Index('idx_user_active', 'is_active', 'created_at'),
    )
    
    @property
    def interests(self):
        """Retourne la liste des objets Interest de l'utilisateur"""
        return [ui.interest for ui in self.user_interests]
    
    @property
    def age(self):
        """Calcule l'âge de l'utilisateur"""
        today = datetime.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}"
    
    def set_password(self, password):
        """Définit le mot de passe hashé"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        try:
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            logger.error(f"Erreur de vérification du mot de passe pour l'utilisateur {self.id}: {e}")
            return False
    
    def update_last_active(self):
        """Met à jour la date de dernière activité"""
        self.last_active = get_timezone_aware_datetime()
        db.session.commit()
    
    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire pour l'API"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'gender': self.gender,
            'city': self.city,
            'bio': self.bio,
            'profile_photo': self.profile_photo,
            'second_photo': self.second_photo,
            'interests': [{'id': i.id, 'name': i.name} for i in self.interests],
            'last_active': self.last_active.isoformat() if self.last_active else None
        }
    
    def __repr__(self):
        return f'<User {self.full_name}>'


class Interest(db.Model):
    """Modèle Centre d'intérêt"""
    __tablename__ = 'interest'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), index=True)
    
    # Relations restaurées pour le fonctionnement de l'application
    user_interests = db.relationship('UserInterest', backref='interest', lazy='dynamic')
    
    def __repr__(self):
        return f'<Interest {self.name}>'


class UserInterest(db.Model):
    """Table d'association entre utilisateurs et centres d'intérêt"""
    __tablename__ = 'user_interest'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    interest_id = db.Column(db.Integer, db.ForeignKey('interest.id'), nullable=False, index=True)
    
    # Contrainte d'unicité
    __table_args__ = (
        db.UniqueConstraint('user_id', 'interest_id', name='uq_user_interest'),
    )
    
    def __repr__(self):
        return f'<UserInterest user_id={self.user_id} interest_id={self.interest_id}>'


class Message(db.Model):
    """Modèle Message"""
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_timezone_aware_datetime, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Index pour optimiser les recherches de conversations
    __table_args__ = (
        db.Index('idx_message_conversation', 'sender_id', 'receiver_id'),
        db.Index('idx_message_expiry', 'expires_at'),
    )
    
    @property
    def time_until_expiry(self):
        """Calcule le temps restant avant expiration"""
        now = get_timezone_aware_datetime()
        
        # Si expires_at n'a pas de fuseau horaire, lui en donner un
        if self.expires_at.tzinfo is None:
            expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = self.expires_at
            
        if expires_at > now:
            diff = expires_at - now
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "Expiré"
    
    def mark_as_read(self):
        """Marque le message comme lu"""
        # La colonne is_read n'existe pas dans la base de données MySQL actuelle
        # self.is_read = True
        # db.session.commit()
        pass
    
    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.receiver_id}>'


class Like(db.Model):
    """Modèle Like"""
    __tablename__ = 'like'
    
    id = db.Column(db.Integer, primary_key=True)
    liker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    liked_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=get_timezone_aware_datetime, index=True)
    
    # Contrainte d'unicité pour éviter les likes en double
    __table_args__ = (
        db.UniqueConstraint('liker_id', 'liked_id', name='uq_like'),
        db.Index('idx_like_match', 'liker_id', 'liked_id'),
    )
    
    def __repr__(self):
        return f'<Like {self.liker_id} -> {self.liked_id}>'


class Match(db.Model):
    """Modèle Match"""
    __tablename__ = 'match'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=get_timezone_aware_datetime, index=True)
    
    # Contrainte d'unicité pour éviter les matches en double
    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='uq_match'),
        db.CheckConstraint('user1_id < user2_id', name='chk_match_order'),
    )
    
    def get_other_user(self, user_id):
        """Retourne l'autre utilisateur dans le match"""
        return self.user2 if self.user1_id == user_id else self.user1
    
    def __repr__(self):
        return f'<Match {self.user1_id} <-> {self.user2_id}>'


class Notification(db.Model):
    """Modèle Notification"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'message', 'like', 'match'
    created_at = db.Column(db.DateTime, default=get_timezone_aware_datetime, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Index pour optimiser les recherches
    __table_args__ = (
        db.Index('idx_notification_user_type', 'user_id', 'type'),
        db.Index('idx_notification_expiry', 'expires_at'),
    )
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        # La colonne is_read n'existe pas dans la base de données MySQL actuelle
        # self.is_read = True
        # db.session.commit()
        pass
    
    def __repr__(self):
        return f'<Notification {self.id} for user {self.user_id}>'