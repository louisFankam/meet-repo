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
                
                # Write debug info to file
                with open('/tmp/debug_login.txt', 'a') as f:
                    f.write(f"DEBUG - Form data received: {dict(request.form)}\n")
                    f.write(f"DEBUG - Email from form: '{email}'\n")
                    f.write(f"DEBUG - Password from form: '{password}'\n")
                
                if not email or not password:
                    flash('Email et mot de passe requis', 'error')
                    return render_template('login.html')
                
                user = UserService.get_user_by_email(email)
                
                # Write debug info to file
                with open('/tmp/debug_login.txt', 'a') as f:
                    f.write(f"DEBUG - User from service: {user}\n")
                    if user:
                        f.write(f"DEBUG - Utilisateur trouvé: {user.email}\n")
                        f.write(f"DEBUG - Mot de passe fourni: {password}\n")
                        f.write(f"DEBUG - Vérification mot de passe: {user.check_password(password)}\n")
                        f.write(f"DEBUG - Utilisateur actif: {user.is_active}\n")
                    else:
                        f.write(f"DEBUG - No user found for email: {email}\n")
                
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
            return render_template('likes.html', received_likes=received_likes)
            
        except Exception as e:
            logger.error(f"Erreur sur la page des likes reçus: {e}")
            flash('Une erreur est survenue', 'error')
            return redirect(url_for('dashboard'))
    
    # Routes API
    @app.route('/api/like/<int:user_id>', methods=['POST'])
    # @login_required  # Temporairement désactivé pour tester
    def api_like_user(user_id):
        """API pour liker un utilisateur"""
        try:
            # Utilisateur hardcoded pour le test
            current_user_id = 1  # ID de Dominique
            
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
    # @login_required  # Temporairement désactivé pour tester
    def api_get_profiles():
        """API pour récupérer les profils disponibles"""
        try:
            # Utilisateur hardcoded pour le test
            current_user_id = 1  # ID de Dominique
            
            # Simuler l'objet user
            from model.models import User
            current_user = User.query.get(current_user_id)
            
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
    # @login_required  # Temporairement désactivé pour tester
    def api_get_matches():
        """API pour récupérer les matches de l'utilisateur"""
        try:
            # Utilisateur hardcoded pour le test
            current_user_id = 1  # ID de Dominique
            
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
    # @login_required  # Temporairement désactivé pour tester
    def api_get_likes_received():
        """API pour récupérer les likes reçus de l'utilisateur"""
        try:
            # Utilisateur hardcoded pour le test
            current_user_id = 1  # ID de Dominique
            
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
    
    @app.route('/api/remove-like/<int:user_id>', methods=['POST'])
    # @login_required  # Temporairement désactivé pour tester
    def api_remove_like(user_id):
        """API pour supprimer un like reçu"""
        try:
            # Utilisateur hardcoded pour le test
            current_user_id = 1  # ID de Dominique
            
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