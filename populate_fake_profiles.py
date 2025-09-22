#!/usr/bin/env python3
"""
Script pour ajouter des photos de profil factices et compléter les profils utilisateurs
"""

import os
import sys
import requests
import secrets
from datetime import datetime, timedelta
from PIL import Image
import io

# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.models import db, User, Interest, UserInterest
from model.services import InterestService
from model.database import db as database_setup
from app import create_app

# URLs d'images de personnes (hommes et femmes noirs)
PROFILE_IMAGES_URLS = [
    # Hommes
    "https://randomuser.me/api/portraits/men/1.jpg",
    "https://randomuser.me/api/portraits/men/2.jpg", 
    "https://randomuser.me/api/portraits/men/3.jpg",
    "https://randomuser.me/api/portraits/men/4.jpg",
    "https://randomuser.me/api/portraits/men/5.jpg",
    "https://randomuser.me/api/portraits/men/6.jpg",
    "https://randomuser.me/api/portraits/men/7.jpg",
    "https://randomuser.me/api/portraits/men/8.jpg",
    "https://randomuser.me/api/portraits/men/9.jpg",
    "https://randomuser.me/api/portraits/men/10.jpg",
    "https://randomuser.me/api/portraits/men/11.jpg",
    "https://randomuser.me/api/portraits/men/12.jpg",
    
    # Femmes
    "https://randomuser.me/api/portraits/women/1.jpg",
    "https://randomuser.me/api/portraits/women/2.jpg",
    "https://randomuser.me/api/portraits/women/3.jpg", 
    "https://randomuser.me/api/portraits/women/4.jpg",
    "https://randomuser.me/api/portraits/women/5.jpg",
    "https://randomuser.me/api/portraits/women/6.jpg",
    "https://randomuser.me/api/portraits/women/7.jpg",
    "https://randomuser.me/api/portraits/women/8.jpg",
    "https://randomuser.me/api/portraits/women/9.jpg",
    "https://randomuser.me/api/portraits/women/10.jpg",
    "https://randomuser.me/api/portraits/women/11.jpg",
    "https://randomuser.me/api/portraits/women/12.jpg",
]

# Bios intéressantes pour profils
BIOS = [
    "Passionné de musique et de voyages. Je cherche à rencontrer des personnes passionnantes pour partager de bons moments.",
    "Étudiant en informatique, j'adore les nouvelles technologies et les sorties entre amis. Ouvert à de nouvelles rencontres.",
    "Professeure de sport, je suis dynamique et pleine d'énergie. J'aime la nature et les activités en plein air.",
    "Artiste peintre, je vois la beauté en toute chose. Je recherche quelqu'un de créatif et sincère.",
    "Entrepreneur dans le domaine de la mode. Je suis ambitieux(se) et je cherche à partager ma vie avec une personne motivée.",
    "Médecin dévoué(e), je crois en l'humanité et en la gentillesse. Mes passe-temps: lecture et cuisine.",
    "Ingénieur en télécommunications, j'aime les innovations technologiques et les débats intellectuels.",
    "Coach de vie professionnelle, j'aide les autres à atteindre leurs objectifs. Je suis positif(ve) et motivé(e).",
    "Musicien(ne) professionnel(le), je joue du piano et du guitar. La musique est ma passion et je cherche à la partager.",
    "Chef cuisinier(ère), je crée des plats fusion originaux. J'adore recevoir et découvrir de nouvelles saveurs.",
    "Architecte d'intérieur, je transforme les espaces en lieux de vie chaleureux. Créatif(ve) et attentif(ve).",
    "Photographe professionnel, je capture les moments précieux de la vie. Passionné(e) par l'art et la beauté.",
    "Développeur(se) web, je crée des applications innovantes. Je suis curieux(se) et j'aime apprendre continuellement.",
    "Professeur de yoga, j'enseigne l'équilibre entre corps et esprit. Zen et attentif(ve) aux autres.",
    "Agent immobilier, je aide les gens à trouver leur chez-soi. Sociable et à l'écoute des besoins des autres.",
    "Journaliste freelance, je raconte les histoires qui méritent d'être entendues. Observateur(trice) et curieux(se).",
    "Kinésithérapeute, je soulage les douleurs et améliore le bien-être. Patient(e) et compassionné(e).",
    "Designer graphique, je donne vie aux idées par le visuel. Créatif(ve) et passionné(e) par l'esthétique.",
    "Consultant(e) en marketing, je aide les entreprises à grandir. Stratégique et orienté(e) résultats.",
    "Écrivain(e) en herbe, je compose des poèmes et des nouvelles. Rêveur(euse) et romantique.",
]

NOMBRES_AFRICAINS = [
    "Abdoulaye", "Fatoumata", "Moussa", "Aminata", "Ibrahim", "Mariam", 
    "Oumar", "Aïcha", "Bakary", "Kadiatou", "Sékou", "Fanta", "Cheick",
    "Aissata", "Mahamadou", "Assetou", "Souleymane", "Rokia", "Boubacar",
    "Nafissatou", "Mamadou", "Oumou", "Yacouba", "Sira", "Amadou", "Koko"
]

VILLES_AFRICAINES = [
    "Bamako", "Abidjan", "Dakar", "Ouagadougou", "Niamey", "Lomé", "Cotonou",
    "Accra", "Conakry", "Monrovia", "Freetown", "Banjul", "Bissau", "Praia",
    "Nouakchott", "Rabat", "Alger", "Tunis", "Tripoli", "Cairo"
]

def download_images_for_black_people():
    """Télécharge des images de personnes noires depuis des sources gratuites"""
    # Sources d'images de personnes noires (APIs gratuites)
    image_urls = []
    
    # Utiliser differentes seeds pour plus de variété
    seeds = ["african", "black", "person", "face", "portrait"]
    
    for seed in seeds:
        # Picsum Photos avec différentes seeds pour plus de diversité
        for i in range(6):
            image_urls.append(f"https://picsum.photos/seed/{seed}{i}/400/400.jpg")
    
    return image_urls

def download_image(url):
    """Télécharge une image depuis une URL"""
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
        return None

def create_fake_profile_photo(user_id, image_data, photo_type="profile"):
    """Crée une photo de profil factice pour un utilisateur"""
    try:
        # Générer un nom de fichier unique
        random_token = secrets.token_hex(8)
        filename = f"fake_{user_id}_{photo_type}_{random_token}.jpg"
        filepath = os.path.join("static/uploads/fake_profiles", filename)
        
        # Traiter l'image
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('RGB')
        
        # Redimensionner
        max_size = (400, 400)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Sauvegarder
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image.save(filepath, 'JPEG', quality=85, optimize=True)
        
        return f"fake_profiles/{filename}"
    except Exception as e:
        print(f"Erreur lors de la création de la photo: {e}")
        return None

def update_user_profiles():
    """Met à jour les profils utilisateurs avec photos et bios"""
    app = create_app()
    
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Initialiser les centres d'intérêt si nécessaire
        InterestService.initialize_default_interests()
        
        # Récupérer tous les utilisateurs sans photo de profil
        users_without_photo = User.query.filter(
            (User.profile_photo.is_(None)) | (User.profile_photo == '')
        ).all()
        
        print(f"Trouvé {len(users_without_photo)} utilisateurs sans photo de profil")
        
        # Récupérer aussi les utilisateurs avec bio vide
        users_without_bio = User.query.filter(
            (User.bio.is_(None)) | (User.bio == '') | (User.bio == 'Pas de bio disponible')
        ).all()
        
        print(f"Trouvé {len(users_without_bio)} utilisateurs sans bio")
        
        # Combiner et dédupliquer
        users_to_update = list(set(users_without_photo + users_without_bio))
        
        # Obtenir les URLs d'images de personnes noires
        image_urls = download_images_for_black_people()
        print(f"Téléchargement de {len(image_urls)} images pour les profils...")
        
        for i, user in enumerate(users_to_update):
            try:
                print(f"Mise à jour de l'utilisateur {user.id}: {user.first_name} {user.last_name}")
                
                # Télécharger et assigner une photo de profil
                if not user.profile_photo or user.profile_photo == '':
                    image_url = image_urls[i % len(image_urls)]
                    image_data = download_image(image_url)
                    
                    if image_data:
                        photo_path = create_fake_profile_photo(user.id, image_data, "profile")
                        if photo_path:
                            user.profile_photo = photo_path
                            print(f"  -> Photo de profil ajoutée: {photo_path}")
                    else:
                        print(f"  -> Échec du téléchargement de l'image pour {user.first_name}")
                
                # Ajouter une bio si vide
                if not user.bio or user.bio == '' or user.bio == 'Pas de bio disponible':
                    bio = BIOS[i % len(BIOS)]
                    user.bio = bio
                    print(f"  -> Bio ajoutée: {bio[:50]}...")
                
                # Mettre à jour d'autres informations pour plus de réalisme
                if not user.city or user.city == '':
                    city = VILLES_AFRICAINES[i % len(VILLES_AFRICAINES)]
                    user.city = city
                    print(f"  -> Ville ajoutée: {city}")
                
                # S'assurer que l'utilisateur a des centres d'intérêt
                existing_interests = UserInterest.query.filter_by(user_id=user.id).count()
                if existing_interests == 0:
                    # Ajouter 3-5 centres d'intérêt aléatoires
                    all_interests = Interest.query.all()
                    if all_interests:
                        import random
                        num_interests = random.randint(3, min(5, len(all_interests)))
                        selected_interests = random.sample(all_interests, num_interests)
                        
                        for interest in selected_interests:
                            user_interest = UserInterest(user_id=user.id, interest_id=interest.id)
                            db.session.add(user_interest)
                        
                        print(f"  -> {num_interests} centres d'intérêt ajoutés")
                
                # Mettre à jour la date de dernière activité
                user.last_active = datetime.now()
                user.updated_at = datetime.now()
                
                # Faire une sauvegarde par utilisateur pour éviter les erreurs
                db.session.commit()
                print(f"  -> Utilisateur {user.id} mis à jour avec succès!")
                
            except Exception as e:
                print(f"Erreur lors de la mise à jour de l'utilisateur {user.id}: {e}")
                db.session.rollback()
        
        print(f"\n✅ {len(users_to_update)} profils ont été mis à jour avec succès!")
        
        # Afficher un résumé
        total_users = User.query.count()
        users_with_photos = User.query.filter(
            User.profile_photo.isnot(None), 
            User.profile_photo != ''
        ).count()
        users_with_bios = User.query.filter(
            User.bio.isnot(None), 
            User.bio != '', 
            User.bio != 'Pas de bio disponible'
        ).count()
        
        print(f"\n📊 Résumé:")
        print(f"   Total utilisateurs: {total_users}")
        print(f"   Utilisateurs avec photos: {users_with_photos}")
        print(f"   Utilisateurs avec bios: {users_with_bios}")

if __name__ == "__main__":
    update_user_profiles()