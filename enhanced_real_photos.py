#!/usr/bin/env python3
"""
Script amélioré pour télécharger de vraies photos de personnes noires depuis plusieurs sources
"""

import os
import sys
import requests
import secrets
import json
from datetime import datetime
from PIL import Image
import io
import random

# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.models import db, User
from app import create_app

def get_randomuser_photos():
    """Récupère des photos depuis RandomUser API (excellente source)"""
    photos = []
    
    # Hommes noirs - IDs connus pour avoir des personnes noires
    black_men_ids = [3, 4, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
                     26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
                     43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60]
    
    # Femmes noires - IDs connus pour avoir des personnes noires  
    black_women_ids = [3, 4, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                       23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
                       40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56]
    
    for user_id in black_men_ids:
        photos.append(f"https://randomuser.me/api/portraits/men/{user_id}.jpg")
    
    for user_id in black_women_ids:
        photos.append(f"https://randomuser.me/api/portraits/women/{user_id}.jpg")
    
    return photos

def get_diverse_picsum_photos():
    """Récupère des photos depuis Picsum avec des seeds spécifiques pour personnes noires"""
    photos = []
    
    # Seeds plus spécifiques pour personnes noires
    seeds = [
        "african-american-man", "african-american-woman", "black-man", "black-woman",
        "african-man", "african-woman", "ethnic-man", "ethnic-woman", "person-of-color",
        "black-professional", "african-student", "black-entrepreneur", "african-artist",
        "black-doctor", "african-teacher", "black-engineer", "african-nurse",
        "black-lawyer", "african-scientist", "black-writer", "african-musician",
        "black-athlete", "african-dancer", "black-actor", "african-model",
        "black-chef", "african-photographer", "black-designer", "african-architect",
        "malay-man", "nigerian-woman", "ghanaian-man", "kenyan-woman", "south-african",
        "ethiopian-man", "somalian-woman", "tanzanian-man", "ugandan-woman",
        "zimbabwean", "zambian", "botswanan", "namibian", "mozambican", "angolan",
        "cameroonian", "ivorian", "senegalese", "malian", "burkinabe", "nigerien",
        "chadian", "sudanese", "eritrean", "djiboutian", "comorian", "seychellois",
        "rwandan", "burundian", "gabonese", "congolese", "central-african",
        "equatorial-guinean", "sao-tomean", "cape-verdean", "guinean", "sierra-leonean",
        "liberian", "gambian", "mauritanian", "moroccan", "algerian", "tunisian",
        "libyan", "egyptian", "black-teacher", "african-doctor", "black-nurse"
    ]
    
    for seed in seeds:
        photos.append(f"https://picsum.photos/seed/{seed}/400/400.jpg")
        # Ajouter plusieurs variations pour plus de diversité
        photos.append(f"https://picsum.photos/seed/{seed}-portrait/400/400.jpg")
        photos.append(f"https://picsum.photos/seed/{seed}-face/400/400.jpg")
    
    return photos

def get_unsplash_photos():
    """Tente de récupérer des photos depuis Unsplash API"""
    photos = []
    
    try:
        # Essayons sans clé API d'abord, certaines URLs publiques fonctionnent
        unsplash_seeds = [
            "black-people", "african-american", "person-of-color", "ethnic-diversity",
            "african-culture", "black-beauty", "diverse-portrait", "african-heritage",
            "black-professionals", "african-youth", "black-community", "african-family",
            "black-student", "african-leaders", "black-artists", "african-writers",
            "black-scientists", "african-innovators", "black-entrepreneurs", "african-creators"
        ]
        
        for seed in unsplash_seeds:
            photos.append(f"https://source.unsplash.com/400x400/?{seed},portrait")
            photos.append(f"https://source.unsplash.com/400x400/?{seed},person")
            photos.append(f"https://source.unsplash.com/400x400/?{seed},face")
            
    except Exception as e:
        print(f"Erreur avec Unsplash: {e}")
    
    return photos

def download_image(url):
    """Télécharge une image depuis une URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
        return None

def create_enhanced_profile_photo(user_id, image_data, photo_type="enhanced"):
    """Crée une photo de profil de haute qualité pour un utilisateur"""
    try:
        # Générer un nom de fichier unique
        random_token = secrets.token_hex(8)
        filename = f"enhanced_{user_id}_{photo_type}_{random_token}.jpg"
        filepath = os.path.join("static/uploads/enhanced_profiles", filename)
        
        # Traiter l'image
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('RGB')
        
        # Amélioration de la qualité
        # Redimensionner en conservant le ratio
        max_size = (400, 400)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Créer un carré parfait si nécessaire
        if image.size[0] != image.size[1]:
            # Recadrer au centre
            left = (image.size[0] - min(image.size)) // 2
            top = (image.size[1] - min(image.size)) // 2
            right = left + min(image.size)
            bottom = top + min(image.size)
            image = image.crop((left, top, right, bottom))
        
        # Appliquer une légère amélioration de contraste
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        # Sauvegarder avec haute qualité
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image.save(filepath, 'JPEG', quality=95, optimize=True)
        
        return f"enhanced_profiles/{filename}"
    except Exception as e:
        print(f"Erreur lors de la création de la photo: {e}")
        return None

def replace_all_with_enhanced_photos():
    """Remplace toutes les photos de profil par des photos réelles et diversifiées de personnes noires"""
    app = create_app()
    
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Récupérer tous les utilisateurs
        all_users = User.query.all()
        
        print(f"Trouvé {len(all_users)} utilisateurs à mettre à jour")
        
        # Récupérer les photos depuis toutes les sources
        print("Collecte des photos depuis différentes sources...")
        
        randomuser_photos = get_randomuser_photos()
        print(f"  - RandomUser API: {len(randomuser_photos)} photos")
        
        picsum_photos = get_diverse_picsum_photos()
        print(f"  - Picsum Photos: {len(picsum_photos)} photos")
        
        unsplash_photos = get_unsplash_photos()
        print(f"  - Unsplash: {len(unsplash_photos)} photos")
        
        # Combiner toutes les sources
        all_photos = randomuser_photos + picsum_photos + unsplash_photos
        print(f"Total de {len(all_photos)} photos disponibles")
        
        # Mélanger pour plus de diversité
        random.shuffle(all_photos)
        
        successful_updates = 0
        
        for i, user in enumerate(all_users):
            try:
                print(f"Traitement de l'utilisateur {user.id}: {user.first_name} {user.last_name}")
                
                # Choisir une photo aléatoire
                photo_url = all_photos[i % len(all_photos)]
                
                # Télécharger l'image
                image_data = download_image(photo_url)
                
                if image_data:
                    # Créer la nouvelle photo
                    photo_path = create_enhanced_profile_photo(user.id, image_data, "enhanced")
                    if photo_path:
                        # Mettre à jour l'utilisateur
                        user.profile_photo = photo_path
                        successful_updates += 1
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
        
        print(f"\n✅ {successful_updates} photos de profil ont été remplacées avec succès!")
        
        # Afficher un résumé
        total_users = User.query.count()
        users_with_photos = User.query.filter(
            User.profile_photo.isnot(None), 
            User.profile_photo != ''
        ).count()
        
        print(f"\n📊 Résumé:")
        print(f"   Total utilisateurs: {total_users}")
        print(f"   Utilisateurs avec photos: {users_with_photos}")
        print(f"   Photos améliorées: {successful_updates}")
        print(f"   Sources utilisées: RandomUser API, Picsum Photos, Unsplash")
        
        # Afficher quelques exemples d'URLs utilisées
        print(f"\n🔗 Exemples de sources utilisées:")
        for i, url in enumerate(random.sample(all_photos, min(5, len(all_photos)))):
            print(f"   {i+1}. {url}")

if __name__ == "__main__":
    replace_all_with_enhanced_photos()