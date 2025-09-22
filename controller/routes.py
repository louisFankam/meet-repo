"""
Routes principales pour l'application Meet
Toutes les routes de l'application
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from email_validator import validate_email, EmailNotValidError
import re
import logging

from model.database import db
from model.models import User, Interest
from model.extensions import get_timezone_aware_datetime
from model.services import (
    UserService, LikeService, MessageService, MatchService, 
    NotificationService, InterestService
)
from model.admin_service import AdminService
from flask_session import Session

logger = logging.getLogger(__name__)




def register_routes(app):
    """Enregistre toutes les routes de l'application"""
    
    @app.route('/')
    def index():
        """Page d'accueil"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Page d'inscription"""
        if request.method == 'POST':
            try:
                # Validation des données
                data = request.form
                
                # Valider l'email
                try:
                    validate_email(data.get('email'))
                except EmailNotValidError:
                    flash('Email invalide', 'error')
                    return render_template('register.html')
                
                # Valider le mot de passe
                password = data.get('password')
                if len(password) < 8:
                    flash('Le mot de passe doit contenir au moins 8 caractères', 'error')
                    return render_template('register.html')
                
                # Vérifier si l'email existe déjà
                if UserService.get_user_by_email(data.get('email')):
                    flash('Cet email est déjà utilisé', 'error')
                    return render_template('register.html')
                
                # Valider la date de naissance
                try:
                    birth_date = datetime.strptime(data.get('birth_date'), '%Y-%m-%d').date()
                except ValueError:
                    flash('Date de naissance invalide', 'error')
                    return render_template('register.html')
                
                # Créer l'utilisateur
                user = UserService.create_user(
                    email=data.get('email'),
                    password=password,
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    birth_date=birth_date,
                    gender=data.get('gender'),
                    interested_in=data.get('interested_in'),
                    city=data.get('city'),
                    bio=data.get('bio')
                )
                
                # Gérer les centres d'intérêt
                interests = request.form.getlist('interests')
                for interest_name in interests:
                    interest = InterestService.get_interest_by_name(interest_name)
                    if interest:
                        InterestService.add_user_interest(user.id, interest.id)
                
                # Gérer les photos
                if 'profile_photo' in request.files:
                    profile_photo = UserService.save_photo(
                        request.files['profile_photo'], user.id, 'profile'
                    )
                    if profile_photo:
                        user.profile_photo = profile_photo
                
                if 'second_photo' in request.files:
                    second_photo = UserService.save_photo(
                        request.files['second_photo'], user.id, 'second'
                    )
                    if second_photo:
                        user.second_photo = second_photo
                
                db.session.commit()
                
                flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                logger.error(f"Erreur lors de l'inscription: {e}")
                flash('Une erreur est survenue lors de l\'inscription', 'error')
                return render_template('register.html')
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Page de connexion"""
        if request.method == 'POST':
            try:
                email = request.form.get('email')
                password = request.form.get('password')
                
                # Retirer logs sensibles en prod
                
                if not email or not password:
                    flash('Email et mot de passe requis', 'error')
                    return render_template('login.html')
                
                user = UserService.get_user_by_email(email)
                
                # Retirer logs sensibles en prod
                
                if user and user.check_password(password) and user.is_active:
                    
                    login_user(user)
                    user.update_last_active()
                    
                    flash('Connexion réussie !', 'success')
                    
                    # Rediriger vers la page demandée ou le dashboard
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('dashboard'))
                else:
                    flash('Email ou mot de passe incorrect', 'error')
                    
            except Exception as e:
                logger.error(f"Erreur lors de la connexion: {e}")
                flash('Une erreur est survenue lors de la connexion', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Déconnexion"""
        logout_user()
        flash('Vous avez été déconnecté', 'success')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Tableau de bord avec profils suggérés"""
        try:
            # Nettoyer les données expirées
            MessageService.cleanup_expired_messages()
            NotificationService.cleanup_expired_notifications()
            
            # Récupérer les paramètres de filtrage
            min_age = request.args.get('min_age', type=int)
            max_age = request.args.get('max_age', type=int)
            city = request.args.get('city', '')
            interest = request.args.get('interest', '')
            
            # Récupérer les profils suggérés
            profiles = UserService.get_suggested_users(
                current_user, min_age, max_age, city, interest, limit=20
            )
            
            # Charger les centres d'intérêt pour chaque profil
            profiles_with_interests = []
            for profile in profiles:
                interests = profile.interests
                profiles_with_interests.append({
                    'user': profile,
                    'interests': interests
                })
            
            # Compter les matches et messages
            matches_count = len(MatchService.get_user_matches(current_user.id))
            messages_count = len(MessageService.get_user_conversations(current_user.id))
            
            return render_template('dashboard_swipe.html', 
                                profiles=profiles_with_interests,
                                matches_count=matches_count,
                                messages_count=messages_count)
            
        except Exception as e:
            logger.error(f"Erreur sur le dashboard: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('index'))
    
    @app.route('/profile/<int:user_id>')
    @login_required
    def profile(user_id):
        """Page de profil"""
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                flash('Utilisateur non trouvé', 'error')
                return redirect(url_for('dashboard'))
            
            # Récupérer les centres d'intérêt
            user_interests = user.interests
            all_interests = InterestService.get_all_interests()
            user_interests_ids = [interest.id for interest in user_interests]
            
            return render_template('profile.html',
                                user=user,
                                user_interests=user_interests,
                                all_interests=all_interests,
                                user_interests_ids=user_interests_ids)
            
        except Exception as e:
            logger.error(f"Erreur sur la page de profil: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/api/profile/update', methods=['POST'])
    @login_required
    def api_update_profile():
        """Met à jour les informations du profil"""
        try:
            data = request.form
            # Champs autorisés
            fields = ['first_name', 'last_name', 'city', 'gender', 'interested_in', 'bio']
            for field in fields:
                if field in data and hasattr(current_user, field):
                    setattr(current_user, field, data.get(field))
            # birth_date
            if 'birth_date' in data and data.get('birth_date'):
                try:
                    current_user.birth_date = datetime.strptime(data.get('birth_date'), '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'success': False, 'error': 'Date de naissance invalide'}), 400
            current_user.updated_at = get_timezone_aware_datetime()
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Erreur mise à jour profil: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500

    @app.route('/api/profile/upload-photo', methods=['POST'])
    @login_required
    def api_upload_photo():
        """Upload une photo de profil ou seconde photo"""
        try:
            if 'photo' not in request.files:
                return jsonify({'success': False, 'error': 'Aucun fichier envoyé'}), 400
            photo = request.files['photo']
            photo_type = request.form.get('type', 'profile')
            filename = UserService.save_photo(photo, current_user.id, 'profile' if photo_type != 'second' else 'second')
            if not filename:
                return jsonify({'success': False, 'error': 'Upload échoué'}), 400
            if photo_type == 'second':
                current_user.second_photo = filename
            else:
                current_user.profile_photo = filename
            db.session.commit()
            return jsonify({'success': True, 'filename': filename})
        except Exception as e:
            logger.error(f"Erreur upload photo: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500

    @app.route('/api/profile/interests', methods=['POST'])
    @login_required
    def api_update_interests():
        """Met à jour les centres d'intérêt de l'utilisateur"""
        try:
            body = request.get_json(silent=True) or {}
            interests = body.get('interests', [])
            # Convertir en entiers
            try:
                interest_ids = [int(i) for i in interests]
            except Exception:
                return jsonify({'success': False, 'error': 'Format intérêts invalide'}), 400
            # Effacer existants puis ajouter la sélection
            from model.models import UserInterest
            UserInterest.query.filter_by(user_id=current_user.id).delete()
            for iid in interest_ids:
                InterestService.add_user_interest(current_user.id, iid)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Erreur mise à jour intérêts: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/messages')
    @login_required
    def messages():
        """Page de messagerie"""
        try:
            # Nettoyer les données expirées
            MessageService.cleanup_expired_messages()
            
            # Récupérer les conversations
            conversations = MessageService.get_user_conversations(current_user.id)
            
            # Conversation sélectionnée
            selected_user_id = request.args.get('user', type=int)
            selected_conversation = None
            
            if selected_user_id:
                # Récupérer les messages de la conversation
                messages = MessageService.get_conversation(current_user.id, selected_user_id)
                other_user = UserService.get_user_by_id(selected_user_id)
                
                if other_user:
                    selected_conversation = {
                        'other_user': other_user,
                        'messages': messages
                    }
            
            return render_template('messages.html',
                                conversations=conversations,
                                selected_conversation=selected_conversation)
            
        except Exception as e:
            logger.error(f"Erreur sur la page de messages: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/matches')
    @login_required
    def matches():
        """Page des matches"""
        try:
            matches = MatchService.get_user_matches(current_user.id)
            return render_template('matches.html', matches=matches)
            
        except Exception as e:
            logger.error(f"Erreur sur la page des matches: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/likes')
    @login_required
    def likes():
        """Page des likes reçus"""
        try:
            received_likes = MatchService.get_received_likes(current_user.id)
            given_likes = LikeService.get_given_likes(current_user.id)
            return render_template('likes.html', received_likes=received_likes, given_likes=given_likes)
            
        except Exception as e:
            logger.error(f"Erreur sur la page des likes reçus: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('dashboard'))

    @app.route('/likes-given')
    @login_required
    def likes_given():
        """Page des likes donnés"""
        try:
            given_likes = LikeService.get_given_likes(current_user.id)
            return render_template('likes_given.html', given_likes=given_likes)
        except Exception as e:
            logger.error(f"Erreur sur la page des likes donnés: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('dashboard'))
    
    # Routes API
    @app.route('/api/like/<int:user_id>', methods=['POST'])
    @login_required
    def api_like_user(user_id):
        """API pour liker un utilisateur"""
        try:
            current_user_id = current_user.id
            
            if current_user_id == user_id:
                return jsonify({'success': False, 'error': 'Vous ne pouvez pas vous liker vous-même'}), 400
            
            liked_user = UserService.get_user_by_id(user_id)
            if not liked_user:
                return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404
            
            like, is_match = LikeService.create_like(current_user_id, user_id)
            
            if not like:
                return jsonify({'success': False, 'error': 'Vous avez déjà liké cet utilisateur'}), 400
            
            return jsonify({
                'success': True,
                'match': is_match,
                'message': 'Like ajouté avec succès !'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors du like: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/profiles', methods=['GET'])
    @login_required
    def api_get_profiles():
        """API pour récupérer les profils disponibles"""
        try:
            current_user_id = current_user.id
            
            if not current_user:
                return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404
            
            # Récupérer les profils suggérés
            profiles = UserService.get_suggested_users(current_user, limit=20)
            
            # Formatter les profils pour le JSON
            profiles_data = []
            for profile in profiles:
                profiles_data.append({
                    'id': profile.id,
                    'first_name': profile.first_name,
                    'age': profile.age,
                    'city': profile.city,
                    'bio': profile.bio,
                    'profile_photo': profile.profile_photo,
                    'interests': [i.name for i in profile.interests]
                })
            
            return jsonify({
                'success': True,
                'profiles': profiles_data,
                'count': len(profiles_data)
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des profils: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/matches', methods=['GET'])
    @login_required
    def api_get_matches():
        """API pour récupérer les matches de l'utilisateur"""
        try:
            current_user_id = current_user.id
            
            # Récupérer les matches
            matches = MatchService.get_user_matches(current_user_id)
            
            # Formatter les matches pour le JSON
            matches_data = []
            for match in matches:
                matched_user = match.user  # MatchDisplay a un attribut 'user'
                matches_data.append({
                    'match_id': match.id if hasattr(match, 'id') else None,
                    'user_id': matched_user.id,
                    'first_name': matched_user.first_name,
                    'age': matched_user.age,
                    'city': matched_user.city,
                    'profile_photo': matched_user.profile_photo
                })
            
            return jsonify({
                'success': True,
                'matches': matches_data,
                'count': len(matches_data)
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des matches: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/likes-received', methods=['GET'])
    @login_required
    def api_get_likes_received():
        """API pour récupérer les likes reçus de l'utilisateur"""
        try:
            current_user_id = current_user.id
            
            # Récupérer les likes reçus
            received_likes = MatchService.get_received_likes(current_user_id)
            
            # Formatter les likes pour le JSON
            likes_data = []
            for like_data in received_likes:
                like = like_data['like']
                user = like_data['user']
                likes_data.append({
                    'like_id': like.id,
                    'user_id': user.id,
                    'first_name': user.first_name,
                    'age': user.age,
                    'city': user.city,
                    'bio': user.bio,
                    'profile_photo': user.profile_photo,
                    'interests': [i.name for i in user.interests],
                    'created_at': like.created_at.isoformat()
                })
            
            return jsonify({
                'success': True,
                'likes': likes_data,
                'count': len(likes_data)
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des likes reçus: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500

    @app.route('/api/likes-given', methods=['GET'])
    @login_required
    def api_get_likes_given():
        """API pour récupérer les likes donnés par l'utilisateur"""
        try:
            likes = LikeService.get_given_likes(current_user.id)
            likes_data = []
            for item in likes:
                like = item['like']
                user = item['user']
                likes_data.append({
                    'like_id': like.id,
                    'user_id': user.id,
                    'first_name': user.first_name,
                    'age': user.age,
                    'city': user.city,
                    'bio': user.bio,
                    'profile_photo': user.profile_photo,
                    'interests': [i.name for i in user.interests],
                    'created_at': like.created_at.isoformat(),
                    'is_match': item['is_match']
                })
            return jsonify({'success': True, 'likes': likes_data, 'count': len(likes_data)})
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des likes donnés: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/remove-like/<int:user_id>', methods=['POST'])
    @login_required
    def api_remove_like(user_id):
        """API pour supprimer un like reçu"""
        try:
            current_user_id = current_user.id
            
            if current_user_id == user_id:
                return jsonify({'success': False, 'error': 'Vous ne pouvez pas supprimer votre propre like'}), 400
            
            # Supprimer le like (l'autre utilisateur a liké l'utilisateur courant)
            success = LikeService.remove_like(user_id, current_user_id)
            
            if success:
                return jsonify({'success': True, 'message': 'Like supprimé avec succès'})
            else:
                return jsonify({'success': False, 'error': 'Like non trouvé'}), 404
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du like: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500

    @app.route('/api/remove-like-given/<int:user_id>', methods=['POST'])
    @login_required
    def api_remove_like_given(user_id):
        """API pour retirer un like donné (vous avez liké l'autre utilisateur)"""
        try:
            success = LikeService.remove_like(current_user.id, user_id)
            if success:
                return jsonify({'success': True, 'message': 'Like retiré avec succès'})
            else:
                return jsonify({'success': False, 'error': 'Like non trouvé'}), 404
        except Exception as e:
            logger.error(f"Erreur lors du retrait du like donné: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/pass/<int:user_id>', methods=['POST'])
    @login_required
    def api_pass_user(user_id):
        """API pour passer un profil"""
        try:
            if current_user.id == user_id:
                return jsonify({'error': 'Vous ne pouvez pas passer votre propre profil'}), 400
            
            passed_user = UserService.get_user_by_id(user_id)
            if not passed_user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
            # Logique pour "passer" un profil (à implémenter)
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Erreur lors du pass: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/send-message', methods=['POST'])
    @login_required
    def api_send_message():
        """API pour envoyer un message"""
        try:
            data = request.get_json()
            receiver_id = data.get('receiver_id')
            content = data.get('content')
            
            if not receiver_id or not content:
                return jsonify({'success': False, 'error': 'Données manquantes'}), 400
            
            if len(content.strip()) == 0:
                return jsonify({'success': False, 'error': 'Message vide'}), 400
            
            message = MessageService.send_message(current_user.id, receiver_id, content)
            
            if not message:
                return jsonify({'success': False, 'error': 'Vous devez matcher pour envoyer un message'}), 400
            
            return jsonify({
                'success': True,
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'expires_at': message.expires_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/messages/<int:user_id>')
    @login_required
    def api_get_messages(user_id):
        """API pour récupérer les messages d'une conversation"""
        try:
            messages = MessageService.get_conversation(current_user.id, user_id)
            
            messages_data = []
            for message in messages:
                messages_data.append({
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'receiver_id': message.receiver_id,
                    'created_at': message.created_at.isoformat(),
                    'expires_at': message.expires_at.isoformat(),
                    'time_until_expiry': message.time_until_expiry
                })
            
            return jsonify({
                'success': True,
                'messages': messages_data
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des messages: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/notifications')
    @login_required
    def api_get_notifications():
        """API pour récupérer les notifications"""
        try:
            notifications = NotificationService.get_user_notifications(current_user.id)
            
            return jsonify({
                'notifications': [
                    {
                        'id': n.id,
                        'message': n.message,
                        'type': n.type,
                        'created_at': n.created_at.isoformat()
                    }
                    for n in notifications
                ]
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500

    @app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
    @login_required
    def api_mark_notification_read(notification_id):
        """Marque une notification comme lue (ici: suppression)"""
        try:
            notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
            if not notification:
                return jsonify({'success': False, 'error': 'Notification introuvable'}), 404
            db.session.delete(notification)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la notification {notification_id}: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/user/<int:user_id>')
    @login_required
    def api_get_user(user_id):
        """API pour récupérer les informations d'un utilisateur"""
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404
            
            return jsonify({
                'success': True,
                'user': user.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
    @app.route('/api/unmatch/<int:user_id>', methods=['POST'])
    @login_required
    def api_unmatch_user(user_id):
        """API pour supprimer un match"""
        try:
            success = MatchService.unmatch_users(current_user.id, user_id)
            
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Erreur lors de la suppression du match'})
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du match: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'}), 500
    
        # Admin Routes - Système séparé
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Page de connexion administration"""
        if request.method == 'POST':
            try:
                email = request.form.get('email')
                password = request.form.get('password')
                
                if not email or not password:
                    flash('Email et mot de passe requis', 'error')
                    return render_template('admin_login.html')
                
                user = UserService.get_user_by_email(email)
                
                if user and user.check_password(password) and user.is_admin and user.is_active:
                    # Utiliser Flask-Login pour l'authentification admin
                    login_user(user)
                    user.update_last_active()
                    
                    # Marquer la session comme admin
                    session['is_admin'] = True
                    session['admin_login_time'] = datetime.now().isoformat()
                    
                    flash('Connexion administrateur réussie !', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Identifiants administrateurs invalides', 'error')
                    
            except Exception as e:
                logger.error(f"Erreur lors de la connexion admin: {e}")
                flash('Une erreur est survenue lors de la connexion', 'error')
        
        return render_template('admin_login.html')
    
    @app.route('/admin/logout')
    def admin_logout():
        """Déconnexion administrateur"""
        # Nettoyer la session admin
        session.pop('is_admin', None)
        session.pop('admin_login_time', None)
        
        logout_user()
        flash('Vous avez été déconnecté de l\'administration', 'success')
        return redirect(url_for('admin_login'))
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """Tableau de bord d'administration"""
        try:
            # Vérifier si c'est une session admin
            if not session.get('is_admin') or not current_user.is_admin:
                logout_user()
                flash('Accès administrateur requis', 'error')
                return redirect(url_for('admin_login'))
            
            # Récupérer les statistiques
            stats = AdminService.get_dashboard_stats()
            
            # Récupérer les utilisateurs récents
            recent_users = AdminService.get_recent_users(limit=10)
            
            # Récupérer les messages récents
            recent_messages = AdminService.get_recent_messages(limit=10)
            
            return render_template('admin_dashboard.html',
                                total_users=stats.get('total_users', 0),
                                active_users=stats.get('active_users', 0),
                                total_matches=stats.get('total_matches', 0),
                                total_messages=stats.get('total_messages', 0),
                                active_conversations=stats.get('active_conversations', 0),
                                activity_rate=stats.get('activity_rate', 0),
                                recent_users=recent_users,
                                recent_messages=recent_messages)
            
        except Exception as e:
            logger.error(f"Erreur sur le dashboard admin: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/users')
    @login_required
    def admin_users():
        """Gestion des utilisateurs"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return redirect(url_for('admin_login'))
            
            page = request.args.get('page', 1, type=int)
            search = request.args.get('search', '')
            filter_status = request.args.get('filter', '')
            
            users = AdminService.get_all_users(page=page, per_page=20, search=search, filter_status=filter_status)
            
            return render_template('admin_users.html', users=users, search=search, filter_status=filter_status)
            
        except Exception as e:
            logger.error(f"Erreur sur la page utilisateurs admin: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/analytics')
    @login_required
    def admin_analytics():
        """Page d'analytique"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return redirect(url_for('admin_login'))
            
            days = request.args.get('days', 30, type=int)
            activity_stats = AdminService.get_activity_stats(days=days)
            
            return render_template('admin_analytics.html', activity_stats=activity_stats, days=days)
            
        except Exception as e:
            logger.error(f"Erreur sur la page analytique admin: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
    @login_required
    def admin_toggle_user(user_id):
        """Activer/désactiver un utilisateur"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Accès non autorisé'})
            
            success, message = AdminService.toggle_user_status(user_id)
            
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'error': message})
                
        except Exception as e:
            logger.error(f"Erreur lors du changement de statut utilisateur: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'})
    
    @app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
    @login_required
    def admin_delete_user(user_id):
        """Supprimer un utilisateur"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Accès non autorisé'})
            
            if user_id == current_user.id:
                return jsonify({'success': False, 'error': 'Vous ne pouvez pas supprimer votre propre compte'})
            
            success, message = AdminService.delete_user(user_id)
            
            if success:
                return jsonify({'success': True, 'message': message})
            else:
                return jsonify({'success': False, 'error': message})
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'})
    
    @app.route('/admin/top-users')
    @login_required
    def admin_top_users():
        """Top utilisateurs"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return redirect(url_for('admin_login'))
            
            metric = request.args.get('metric', 'matches')
            top_users = AdminService.get_top_users(metric=metric, limit=10)
            
            return render_template('admin_top_users.html', top_users=top_users, metric=metric)
            
        except Exception as e:
            logger.error(f"Erreur sur la page top utilisateurs admin: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('admin_dashboard'))
    
    # Admin API Routes
    @app.route('/api/admin/cleanup', methods=['POST'])
    @login_required
    def api_admin_cleanup():
        """API pour nettoyer les données expirées"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Accès non autorisé'})
            
            result = AdminService.cleanup_expired_data()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f"Nettoyage terminé: {result['total_cleaned']} éléments supprimés",
                    'details': result
                })
            else:
                return jsonify({'success': False, 'error': result['error']})
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des données: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'})
    
    @app.route('/api/admin/export-data')
    @login_required
    def api_admin_export_data():
        """API pour exporter les données"""
        try:
            if not session.get('is_admin') or not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Accès non autorisé'})
            
            format_type = request.args.get('format', 'json')
            data = AdminService.export_data(format=format_type)
            
            if not data:
                return jsonify({'success': False, 'error': 'Erreur lors de l\'export'})
            
            if format_type == 'json':
                return jsonify(data)
            else:
                return jsonify({'success': False, 'error': 'Format non supporté'})
                
        except Exception as e:
            logger.error(f"Erreur lors de l'export des données: {e}")
            return jsonify({'success': False, 'error': 'Une erreur est survenue'})
    
    @app.route('/favicon.ico')
    def favicon():
        """Route pour le favicon"""
        return '', 204
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Gestion des erreurs 404"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        """Gestion des erreurs 500"""
        logger.error(f"Erreur 500: {e}")
        return render_template('errors/500.html'), 500


def register_filters(app):
    """Enregistre les filtres personnalisés"""
    
    @app.template_filter('timeago')
    def timeago_filter(date):
        """Convertir une date en format 'il y a X temps'"""
        now = get_timezone_aware_datetime()
        
        # Si la date est une chaîne, la convertir
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        # Si la date n'a pas de fuseau horaire, lui en donner un
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        
        diff = now - date
        
        if diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "À l'instant"


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)