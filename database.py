#!/usr/bin/env python3
"""
Script de création et d'initialisation de la base de données MySQL pour l'application Meet
"""

import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

def create_database():
    """Créer la base de données et les tables"""
    
    # Configuration de connexion MySQL
    config = {
        'host': 'localhost',
        'user': 'root',  # Utilisateur root par défaut
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    try:
        # Connexion à MySQL
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("✅ Connexion à MySQL établie")
        
        # Créer la base de données
        cursor.execute("CREATE DATABASE IF NOT EXISTS dating_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ Base de données 'dating_app' créée ou déjà existante")
        
        # Utiliser la base de données
        cursor.execute("USE dating_app")
        
        # Créer les tables
        create_tables(cursor)
        
        # Insérer les données initiales
        insert_initial_data(cursor)
        
        # Valider les changements
        connection.commit()
        print("✅ Base de données initialisée avec succès")
        
    except Error as e:
        print(f"❌ Erreur MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Connexion MySQL fermée")

def create_tables(cursor):
    """Créer toutes les tables nécessaires"""
    
    # Table des utilisateurs
    users_table = """
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        birth_date DATE NOT NULL,
        gender VARCHAR(20) NOT NULL,
        interested_in VARCHAR(20) NOT NULL,
        city VARCHAR(100) NOT NULL,
        bio TEXT,
        profile_photo VARCHAR(255),
        second_photo VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_city (city),
        INDEX idx_gender (gender),
        INDEX idx_interested_in (interested_in),
        INDEX idx_birth_date (birth_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # Table des centres d'intérêt
    interests_table = """
    CREATE TABLE IF NOT EXISTS interest (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        category VARCHAR(50),
        INDEX idx_name (name),
        INDEX idx_category (category)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # Table de liaison utilisateur-intérêts
    user_interests_table = """
    CREATE TABLE IF NOT EXISTS user_interest (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        interest_id INT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
        FOREIGN KEY (interest_id) REFERENCES interest(id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_interest (user_id, interest_id),
        INDEX idx_user_id (user_id),
        INDEX idx_interest_id (interest_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # Table des messages
    messages_table = """
    CREATE TABLE IF NOT EXISTS message (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sender_id INT NOT NULL,
        receiver_id INT NOT NULL,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES user(id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES user(id) ON DELETE CASCADE,
        INDEX idx_sender_id (sender_id),
        INDEX idx_receiver_id (receiver_id),
        INDEX idx_created_at (created_at),
        INDEX idx_expires_at (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # Table des likes
    likes_table = """
    CREATE TABLE IF NOT EXISTS `like` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        liker_id INT NOT NULL,
        liked_id INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (liker_id) REFERENCES user(id) ON DELETE CASCADE,
        FOREIGN KEY (liked_id) REFERENCES user(id) ON DELETE CASCADE,
        UNIQUE KEY unique_like (liker_id, liked_id),
        INDEX idx_liker_id (liker_id),
        INDEX idx_interest_id (liked_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # Table des notifications
    notifications_table = """
    CREATE TABLE IF NOT EXISTS notification (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        message VARCHAR(255) NOT NULL,
        type VARCHAR(50) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_type (type),
        INDEX idx_created_at (created_at),
        INDEX idx_expires_at (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # Exécuter la création des tables
    tables = [
        ("users", users_table),
        ("interests", interests_table),
        ("user_interests", user_interests_table),
        ("messages", messages_table),
        ("likes", likes_table),
        ("notifications", notifications_table)
    ]
    
    for table_name, table_sql in tables:
        try:
            cursor.execute(table_sql)
            print(f"✅ Table '{table_name}' créée ou déjà existante")
        except Error as e:
            print(f"❌ Erreur lors de la création de la table '{table_name}': {e}")

def insert_initial_data(cursor):
    """Insérer les données initiales (centres d'intérêt)"""
    
    # Centres d'intérêt par défaut
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
    
    # Insérer les centres d'intérêt
    for interest_name, category in interests:
        try:
            cursor.execute(
                "INSERT IGNORE INTO interest (name, category) VALUES (%s, %s)",
                (interest_name, category)
            )
        except Error as e:
            print(f"⚠️  Erreur lors de l'insertion de l'intérêt '{interest_name}': {e}")
    
    print("✅ Centres d'intérêt initiaux insérés")

def create_sample_users(cursor):
    """Créer quelques utilisateurs de test (optionnel)"""
    
    sample_users = [
        {
            'email': 'marie.dubois@example.com',
            'password_hash': 'hashed_password_123',  # En production, utiliser bcrypt
            'first_name': 'Marie',
            'last_name': 'Dubois',
            'birth_date': '1995-03-15',
            'gender': 'femme',
            'interested_in': 'hommes',
            'city': 'Paris',
            'bio': 'Passionnée de voyage et de photographie. J\'aime découvrir de nouveaux endroits et rencontrer des personnes intéressantes.'
        },
        {
            'email': 'pierre.martin@example.com',
            'password_hash': 'hashed_password_456',
            'first_name': 'Pierre',
            'last_name': 'Martin',
            'birth_date': '1992-07-22',
            'gender': 'homme',
            'interested_in': 'femmes',
            'city': 'Lyon',
            'bio': 'Sportif et amateur de cuisine. J\'aime les défis et les nouvelles expériences.'
        }
    ]
    
    for user in sample_users:
        try:
            cursor.execute("""
                INSERT IGNORE INTO user 
                (email, password_hash, first_name, last_name, birth_date, gender, interested_in, city, bio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user['email'], user['password_hash'], user['first_name'], user['last_name'],
                user['birth_date'], user['gender'], user['interested_in'], user['city'], user['bio']
            ))
        except Error as e:
            print(f"⚠️  Erreur lors de l'insertion de l'utilisateur '{user['first_name']}': {e}")
    
    print("✅ Utilisateurs de test créés")

def main():
    """Fonction principale"""
    print("🚀 Initialisation de la base de données Meet...")
    print("=" * 50)
    
    create_database()
    
    print("\n" + "=" * 50)
    print("🎉 Initialisation terminée !")
    print("\nProchaines étapes:")
    print("1. Modifiez la configuration dans config.py si nécessaire")
    print("2. Lancez l'application avec: python run.py")
    print("3. Accédez à http://localhost:5000")

if __name__ == "__main__":
    main()
