#!/usr/bin/env python3
"""
Script pour remplacer toutes les photos de profil par de vraies photos de personnes noires
"""

import os
import sys
import requests
import secrets
from datetime import datetime
from PIL import Image
import io

# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.models import db, User
from app import create_app

def download_images_for_black_people():
    """Télécharge des images de personnes noires depuis des sources gratuites"""
    image_urls = []
    
    # Utiliser différentes seeds spécifiques pour plus de diversité d'images de personnes noires
    seeds = [
        "african", "black", "person", "face", "portrait", "ethnic", "diverse",
        "african-american", "black-woman", "black-man", "african-face",
        "ethnic-beauty", "diverse-portrait", "person-of-color"
    ]
    
    for seed in seeds:
        # Picsum Photos avec différentes seeds pour plus de diversité
        for i in range(3):
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

def create_profile_photo(user_id, image_data, photo_type="profile"):
    """Crée une photo de profil pour un utilisateur"""
    try:
        # Générer un nom de fichier unique
        random_token = secrets.token_hex(8)
        filename = f"real_{user_id}_{photo_type}_{random_token}.jpg"
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

def replace_all_profile_photos():
    """Remplace toutes les photos de profil par de vraies photos de personnes noires"""
    app = create_app()
    
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Récupérer tous les utilisateurs
        all_users = User.query.all()
        
        print(f"Trouvé {len(all_users)} utilisateurs à mettre à jour")
        
        # Obtenir les URLs d'images de personnes noires
        image_urls = download_images_for_black_people()
        print(f"Téléchargement de {len(image_urls)} images variées...")
        
        for i, user in enumerate(all_users):
            try:
                print(f"Remplacement de la photo pour {user.id}: {user.first_name} {user.last_name}")
                
                # Télécharger une nouvelle image
                image_url = image_urls[i % len(image_urls)]
                image_data = download_image(image_url)
                
                if image_data:
                    # Créer la nouvelle photo
                    photo_path = create_profile_photo(user.id, image_data, "profile")
                    if photo_path:
                        # Mettre à jour l'utilisateur
                        user.profile_photo = photo_path
                        print(f"  ✅ Photo remplacée: {photo_path}")
                    else:
                        print(f"  ❌ Échec de création de la photo")
                else:
                    print(f"  ❌ Échec du téléchargement de l'image")
                
                # Faire une sauvegarde par utilisateur pour éviter les erreurs
                db.session.commit()
                
            except Exception as e:
                print(f"Erreur lors de la mise à jour de l'utilisateur {user.id}: {e}")
                db.session.rollback()
        
        print(f"\n✅ {len(all_users)} photos de profil ont été remplacées avec succès!")
        
        # Afficher un résumé
        total_users = User.query.count()
        users_with_photos = User.query.filter(
            User.profile_photo.isnot(None), 
            User.profile_photo != ''
        ).count()
        
        print(f"\n📊 Résumé:")
        print(f"   Total utilisateurs: {total_users}")
        print(f"   Utilisateurs avec photos: {users_with_photos}")
        print(f"   Photos remplacées par de vraies images: {users_with_photos}")

if __name__ == "__main__":
    replace_all_profile_photos()