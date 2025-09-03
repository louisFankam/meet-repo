from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SelectField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone
import os
import bcrypt
from PIL import Image
import io
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from dotenv import load_dotenv

load_dotenv()

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'votre-clé-secrète-ici')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///meet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialisation des extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Scheduler pour le nettoyage automatique
scheduler = BackgroundScheduler()
scheduler.start()

# Arrêter le scheduler à la fermeture de l'app
atexit.register(lambda: scheduler.shutdown())

# Modèles de base de données
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    interested_in = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    second_photo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    interests = db.relationship('UserInterest', backref='user', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    likes_given = db.relationship('Like', foreign_keys='Like.liker_id', backref='liker', lazy=True)
    likes_received = db.relationship('Like', foreign_keys='Like.liked_id', backref='liked', lazy=True)
    
    @property
    def age(self):
        today = datetime.now().date()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))

class UserInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    interest_id = db.Column(db.Integer, db.ForeignKey('interest.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    @property
    def time_until_expiry(self):
        now = datetime.utcnow()
        if self.expires_at > now:
            diff = self.expires_at - now
            hours = diff.total_seconds() // 3600
            minutes = (diff.total_seconds() % 3600) // 60
            if hours > 0:
                return f"{int(hours)}h {int(minutes)}m"
            else:
                return f"{int(minutes)}m"
        return "Expiré"

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    liker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    liked_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'message', 'like', 'match'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Fonctions utilitaires
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_photo(file, user_id, photo_type):
    if file and allowed_file(file.filename):
        # Générer un nom de fichier unique
        filename = f"{user_id}_{photo_type}_{int(datetime.utcnow().timestamp())}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
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

def create_notification(user_id, message, notification_type):
    expires_at = datetime.utcnow() + timedelta(hours=24)
    notification = Notification(
        user_id=user_id,
        message=message,
        type=notification_type,
        expires_at=expires_at
    )
    db.session.add(notification)
    db.session.commit()

def cleanup_expired_data():
    """Nettoyer les messages et notifications expirés"""
    now = datetime.utcnow()
    
    # Supprimer les messages expirés
    expired_messages = Message.query.filter(Message.expires_at < now).all()
    for message in expired_messages:
        db.session.delete(message)
    
    # Supprimer les notifications expirées
    expired_notifications = Notification.query.filter(Notification.expires_at < now).all()
    for notification in expired_notifications:
        db.session.delete(notification)
    
    db.session.commit()
    print(f"Nettoyage effectué: {len(expired_messages)} messages et {len(expired_notifications)} notifications supprimés")

def schedule_cleanup():
    """Programme le nettoyage automatique toutes les heures"""
    scheduler.add_job(
        func=cleanup_expired_data,
        trigger=IntervalTrigger(hours=1),
        id='cleanup_expired_data',
        name='Nettoyage automatique des données expirées',
        replace_existing=True
    )
    print("Nettoyage automatique programmé toutes les heures")



# Routes principales
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Validation des données
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_date = request.form.get('birth_date')
        gender = request.form.get('gender')
        interested_in = request.form.get('interested_in')
        city = request.form.get('city')
        bio = request.form.get('bio')
        interests = request.form.getlist('interests')
        
        # Validation
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'error')
            return render_template('register.html')
        
        # Créer l'utilisateur
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(
            email=email,
            password_hash=password_hash.decode('utf-8'),
            first_name=first_name,
            last_name=last_name,
            birth_date=datetime.strptime(birth_date, '%Y-%m-%d').date(),
            gender=gender,
            interested_in=interested_in,
            city=city,
            bio=bio
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Gérer les centres d'intérêt
        for interest_name in interests:
            interest = Interest.query.filter_by(name=interest_name).first()
            if interest:
                user_interest = UserInterest(user_id=user.id, interest_id=interest.id)
                db.session.add(user_interest)
        
        # Gérer les photos
        if 'profile_photo' in request.files:
            profile_photo = save_photo(request.files['profile_photo'], user.id, 'profile')
            if profile_photo:
                user.profile_photo = profile_photo
        
        if 'second_photo' in request.files:
            second_photo = save_photo(request.files['second_photo'], user.id, 'second')
            if second_photo:
                user.second_photo = second_photo
        
        db.session.commit()
        
        flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            user.last_active = datetime.utcnow()
            db.session.commit()
            
            flash('Connexion réussie !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Nettoyer les données expirées
    cleanup_expired_data()
    
    # Récupérer les paramètres de filtrage
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    city = request.args.get('city', '')
    interest = request.args.get('interest', '')
    
    # Construire la requête - exclure l'utilisateur actuel et filtrer par genre d'intérêt
    # Normaliser les genres pour éviter les problèmes de casse
    interested_gender = current_user.interested_in.lower()
    if interested_gender == 'femmes':
        interested_gender = 'femme'
    elif interested_gender == 'hommes':
        interested_gender = 'homme'
    
    query = User.query.filter(
        User.id != current_user.id,
        db.func.lower(User.gender) == interested_gender
    )
    
    # Filtres
    if min_age:
        min_date = datetime.now().date() - timedelta(days=min_age*365)
        query = query.filter(User.birth_date <= min_date)
    
    if max_age:
        max_date = datetime.now().date() - timedelta(days=max_age*365)
        query = query.filter(User.birth_date >= max_date)
    
    if city:
        query = query.filter(User.city.ilike(f'%{city}%'))
    
    if interest:
        query = query.join(UserInterest).join(Interest).filter(Interest.name == interest)
    

    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Compter les matches et messages
    matches_count = Like.query.filter(
        Like.liker_id == current_user.id,
        Like.liked_id.in_(
            db.session.query(Like.liker_id).filter(Like.liked_id == current_user.id)
        )
    ).count()
    
    messages_count = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).count()
    
    return render_template('dashboard.html', 
                         profiles=pagination.items,
                         pagination=pagination,
                         matches_count=matches_count,
                         messages_count=messages_count)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Récupérer les centres d'intérêt
    user_interests = [ui.interest for ui in user.interests]
    all_interests = Interest.query.all()
    user_interests_ids = [ui.interest_id for ui in user.interests]
    
    return render_template('profile.html',
                         user=user,
                         user_interests=user_interests,
                         all_interests=all_interests,
                         user_interests_ids=user_interests_ids)

@app.route('/messages')
@login_required
def messages():
    # Nettoyer les données expirées
    cleanup_expired_data()
    
    # Récupérer les conversations
    conversations = []
    
    # Messages envoyés et reçus
    sent_messages = Message.query.filter_by(sender_id=current_user.id).all()
    received_messages = Message.query.filter_by(receiver_id=current_user.id).all()
    
    # Créer un dictionnaire des conversations
    conversation_dict = {}
    
    for message in sent_messages:
        other_user_id = message.receiver_id
        if other_user_id not in conversation_dict:
            conversation_dict[other_user_id] = {
                'other_user': User.query.get(other_user_id),
                'last_message': message,
                'unread_count': 0
            }
        elif message.created_at > conversation_dict[other_user_id]['last_message'].created_at:
            conversation_dict[other_user_id]['last_message'] = message
    
    for message in received_messages:
        other_user_id = message.sender_id
        if other_user_id not in conversation_dict:
            conversation_dict[other_user_id] = {
                'other_user': User.query.get(other_user_id),
                'last_message': message,
                'unread_count': 1
            }
        elif message.created_at > conversation_dict[other_user_id]['last_message'].created_at:
            conversation_dict[other_user_id]['last_message'] = message
            conversation_dict[other_user_id]['unread_count'] = 1
    
    # Convertir en liste et trier par date du dernier message
    conversations = list(conversation_dict.values())
    conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)
    
    # Conversation sélectionnée
    selected_user_id = request.args.get('user', type=int)
    selected_conversation = None
    
    if selected_user_id:
        # Récupérer les messages de la conversation
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == selected_user_id)) |
            ((Message.sender_id == selected_user_id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at).all()
        
        selected_conversation = {
            'other_user': User.query.get(selected_user_id),
            'messages': messages
        }
    
    return render_template('messages.html',
                         conversations=conversations,
                         selected_conversation=selected_conversation)

@app.route('/matches')
@login_required
def matches():
    # Récupérer les matches (likes mutuels)
    matches = []
    
    # Utilisateurs que l'utilisateur actuel a likés
    liked_users = db.session.query(Like.liked_id).filter(Like.liker_id == current_user.id).subquery()
    
    # Utilisateurs qui ont liké l'utilisateur actuel
    users_who_liked = db.session.query(Like.liker_id).filter(Like.liked_id == current_user.id).subquery()
    
    # Matches (intersection)
    match_query = User.query.filter(
        User.id.in_(liked_users),
        User.id.in_(users_who_liked)
    )
    
    for user in match_query.all():
        # Récupérer le dernier message échangé
        last_message = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == user.id)) |
            ((Message.sender_id == user.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.desc()).first()
        
        matches.append({
            'user': user,
            'last_message': last_message,
            'match_date': Like.query.filter_by(
                liker_id=current_user.id, 
                liked_id=user.id
            ).first().created_at
        })
    
    # Trier par date de match
    matches.sort(key=lambda x: x['match_date'], reverse=True)
    
    return render_template('matches.html', matches=matches)

# Routes API
@app.route('/api/like/<int:user_id>', methods=['POST'])
@login_required
def like_user(user_id):
    if current_user.id == user_id:
        return jsonify({'success': False, 'error': 'Vous ne pouvez pas vous liker vous-même'}), 400
    
    # Vérifier si l'utilisateur existe
    liked_user = User.query.get(user_id)
    if not liked_user:
        return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404
    
    # Vérifier si le like existe déjà
    existing_like = Like.query.filter_by(
        liker_id=current_user.id,
        liked_id=user_id
    ).first()
    
    if existing_like:
        return jsonify({'success': False, 'error': 'Vous avez déjà liké cet utilisateur'}), 400
    
    # Créer le like
    new_like = Like(liker_id=current_user.id, liked_id=user_id)
    db.session.add(new_like)
    
    # Vérifier si c'est un match mutuel
    mutual_like = Like.query.filter_by(
        liker_id=user_id,
        liked_id=current_user.id
    ).first()
    
    is_match = False
    if mutual_like:
        is_match = True
        # Créer une notification pour le match
        create_notification(
            user_id=user_id,
            message=f"Vous avez un nouveau match avec {current_user.first_name} !",
            notification_type='match'
        )
        
        # Créer aussi une notification pour l'utilisateur actuel
        create_notification(
            user_id=current_user.id,
            message=f"Vous avez un nouveau match avec {liked_user.first_name} !",
            notification_type='match'
        )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'match': is_match,
        'message': 'Like ajouté avec succès !'
    })

@app.route('/api/pass/<int:user_id>', methods=['POST'])
@login_required
def pass_user(user_id):
    if current_user.id == user_id:
        return jsonify({'error': 'Vous ne pouvez pas passer votre propre profil'}), 400
    
    # Vérifier si l'utilisateur existe
    passed_user = User.query.get(user_id)
    if not passed_user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    # Créer un enregistrement de "pass" pour éviter de montrer à nouveau ce profil
    # (optionnel, pour améliorer l'expérience utilisateur)
    
    return jsonify({'success': True})

@app.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not receiver_id or not content:
        return jsonify({'success': False, 'error': 'Données manquantes'})
    
    # Vérifier que c'est un match
    mutual_like = (
        Like.query.filter_by(liker_id=current_user.id, liked_id=receiver_id).first() and
        Like.query.filter_by(liker_id=receiver_id, liked_id=current_user.id).first()
    )
    
    if not mutual_like:
        return jsonify({'success': False, 'error': 'Vous devez matcher pour envoyer un message'})
    
    # Créer le message
    expires_at = datetime.utcnow() + timedelta(hours=24)
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        expires_at=expires_at
    )
    
    db.session.add(message)
    
    # Créer une notification
    receiver = User.query.get(receiver_id)
    create_notification(
        receiver_id,
        f"Nouveau message de {current_user.first_name}",
        'message'
    )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'expires_at': message.expires_at.isoformat()
        }
    })

@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.expires_at > datetime.utcnow()
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
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

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()
    
    if notification:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Notification non trouvée'})

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    # Mettre à jour les informations du profil
    current_user.first_name = request.form.get('first_name')
    current_user.last_name = request.form.get('last_name')
    current_user.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date()
    current_user.gender = request.form.get('gender')
    current_user.interested_in = request.form.get('interested_in')
    current_user.city = request.form.get('city')
    current_user.bio = request.form.get('bio')
    
    db.session.commit()
    
    flash('Profil mis à jour avec succès !', 'success')
    return jsonify({'success': True})

@app.route('/api/profile/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'})
    
    photo_type = request.form.get('type', 'profile')
    
    if photo_type == 'profile':
        current_user.profile_photo = save_photo(request.files['photo'], current_user.id, 'profile')
    elif photo_type == 'second':
        current_user.second_photo = save_photo(request.files['photo'], current_user.id, 'second')
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/profile/interests', methods=['POST'])
@login_required
def update_interests():
    data = request.get_json()
    interests = data.get('interests', [])
    
    # Supprimer les anciens intérêts
    UserInterest.query.filter_by(user_id=current_user.id).delete()
    
    # Ajouter les nouveaux intérêts
    for interest_id in interests:
        user_interest = UserInterest(user_id=current_user.id, interest_id=int(interest_id))
        db.session.add(user_interest)
    
    db.session.commit()
    
    return jsonify({'success': True})



@app.route('/api/user/<int:user_id>')
@login_required
def get_user_info(user_id):
    """Récupère les informations d'un utilisateur pour le modal de profil"""
    user = User.query.get_or_404(user_id)
    
    # Récupérer les centres d'intérêt
    user_interests = [{'id': ui.interest.id, 'name': ui.interest.name} for ui in user.interests]
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'age': user.age,
            'gender': user.gender,
            'city': user.city,
            'bio': user.bio,
            'profile_photo': user.profile_photo,
            'second_photo': user.second_photo,
            'interests': user_interests
        }
    })

@app.route('/api/cleanup', methods=['POST'])
@login_required
def api_cleanup():
    """API pour nettoyer les données expirées (admin uniquement)"""
    if current_user.email != 'admin@meet.com':
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    
    cleanup_expired_data()
    return jsonify({'success': True})

@app.route('/api/export-data')
@login_required
def export_data():
    """Export des données en CSV (admin uniquement)"""
    if current_user.email != 'admin@meet.com':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['Type', 'ID', 'Détails', 'Date'])
    
    # Utilisateurs
    users = User.query.all()
    for user in users:
        writer.writerow(['Utilisateur', user.id, f"{user.first_name} {user.last_name} - {user.email}", user.created_at])
    
    # Messages
    messages = Message.query.all()
    for message in messages:
        writer.writerow(['Message', message.id, f"De {message.sender.first_name} à {message.receiver.first_name}", message.created_at])
    
    # Likes
    likes = Like.query.all()
    for like in likes:
        writer.writerow(['Like', like.id, f"{like.liker.first_name} → {like.liked.first_name}", like.created_at])
    
    output.seek(0)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=meet_data_export.csv'}
    )

@app.route('/admin')
@login_required
def admin():
    """Interface d'administration - accessible uniquement aux administrateurs"""
    # Vérifier si l'utilisateur est admin (email spécifique pour l'exemple)
    if current_user.email != 'admin@meet.com':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    # Statistiques
    total_users = User.query.count()
    total_matches = db.session.query(Like).join(
        Like, Like.liked_id == Like.liker_id
    ).filter(
        Like.liker_id != Like.liked_id
    ).count() // 2  # Diviser par 2 car chaque match compte deux fois
    
    total_messages = Message.query.count()
    active_conversations = db.session.query(
        db.func.count(db.func.distinct(
            db.case(
                (Message.sender_id < Message.receiver_id, 
                 db.func.concat(Message.sender_id, '-', Message.receiver_id)),
                else_=db.func.concat(Message.receiver_id, '-', Message.sender_id)
            )
        ))
    ).scalar()
    
    # Utilisateurs récents
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Messages récents
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template('admin.html',
                         total_users=total_users,
                         total_matches=total_matches,
                         total_messages=total_messages,
                         active_conversations=active_conversations,
                         recent_users=recent_users,
                         recent_messages=recent_messages)

@app.route('/api/unmatch/<int:user_id>', methods=['POST'])
@login_required
def unmatch_user(user_id):
    # Supprimer les likes mutuels
    Like.query.filter_by(liker_id=current_user.id, liked_id=user_id).delete()
    Like.query.filter_by(liker_id=user_id, liked_id=current_user.id).delete()
    
    # Supprimer tous les messages échangés
    Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).delete()
    
    db.session.commit()
    
    return jsonify({'success': True})

# Filtres Jinja2
@app.template_filter('timeago')
def timeago_filter(date):
    """Convertir une date en format 'il y a X temps'"""
    now = datetime.utcnow()
    if isinstance(date, str):
        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    
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
    with app.app_context():
        # Créer les tables et insérer les données initiales
        db.create_all()
        
        # Insérer les centres d'intérêt s'ils n'existent pas
        if not Interest.query.first():
            interests = [
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
            
            for name, category in interests:
                interest = Interest(name=name, category=category)
                db.session.add(interest)
            
            db.session.commit()
            print("✅ Centres d'intérêt initiaux insérés")
        
        # Programmer le nettoyage automatique
        schedule_cleanup()
        print("✅ Nettoyage automatique programmé")
    
    app.run(debug=True)
