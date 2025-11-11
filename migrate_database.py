#!/usr/bin/env python3
"""
Script de migration pour ajouter les colonnes manquantes pour les read receipts et le statut en ligne
"""

import pymysql
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_db_connection():
    """Établir une connexion à la base de données"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'root'),
        database=os.getenv('DB_NAME', 'meet_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def run_migration():
    """Exécuter la migration"""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            print("Ajout des colonnes pour les messages...")
            
            # Vérifier si la colonne is_read existe dans la table message
            cursor.execute("SHOW COLUMNS FROM message LIKE 'is_read'")
            result = cursor.fetchone()
            if not result:
                cursor.execute("""
                    ALTER TABLE message 
                    ADD COLUMN is_read BOOLEAN DEFAULT FALSE,
                    ADD COLUMN read_at DATETIME NULL,
                    ADD INDEX idx_message_read (is_read, receiver_id)
                """)
                print("Colonnes is_read et read_at ajoutées à la table message")
            else:
                print("Les colonnes pour les messages existent déjà")
            
            # Vérifier si la colonne is_online existe dans la table user
            cursor.execute("SHOW COLUMNS FROM user LIKE 'is_online'")
            result = cursor.fetchone()
            if not result:
                cursor.execute("""
                    ALTER TABLE user 
                    ADD COLUMN is_online BOOLEAN DEFAULT FALSE,
                    ADD COLUMN last_seen DATETIME NULL,
                    ADD INDEX idx_user_online (is_online)
                """)
                print("Colonnes is_online et last_seen ajoutées à la table user")
            else:
                print("Les colonnes pour les utilisateurs existent déjà")
            
        # Commit des changements
        conn.commit()
        print("Migration terminée avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de la migration: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()