#!/usr/bin/env python3
"""
Script de migration pour corriger les noms de tables SQL réservées
Renomme 'like' -> 'likes' et 'match' -> 'matches'
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from model.models import db
from sqlalchemy import text
from model.models import *

def migrate_tables():
    """Effectue la migration des tables"""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/meet_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    with app.app_context():
        try:
            # Vérifier si les tables existent avec les anciens noms
            result = db.session.execute(text("SHOW TABLES LIKE 'like'"))
            like_table_exists = result.fetchone() is not None
            
            result = db.session.execute(text("SHOW TABLES LIKE 'match'"))
            match_table_exists = result.fetchone() is not None
            
            if like_table_exists:
                print("Renommage de la table 'like' en 'likes'...")
                db.session.execute(text("RENAME TABLE `like` TO `likes`"))
                db.session.commit()
                print("✅ Table 'like' renommée en 'likes'")
            else:
                print("ℹ️  La table 'like' n'existe pas, probablement déjà renommée")
            
            if match_table_exists:
                print("Renommage de la table 'match' en 'matches'...")
                db.session.execute(text("RENAME TABLE `match` TO `matches`"))
                db.session.commit()
                print("✅ Table 'match' renommée en 'matches'")
            else:
                print("ℹ️  La table 'match' n'existe pas, probablement déjà renommée")
            
            print("\n🎉 Migration terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("Début de la migration des noms de tables...")
    success = migrate_tables()
    
    if success:
        print("\n✅ Migration réussie!")
        print("Les tables 'like' et 'match' ont été renommées en 'likes' et 'matches'")
        print("Cela corrige les erreurs de syntaxe SQL dues aux mots réservés.")
    else:
        print("\n❌ Échec de la migration!")
        sys.exit(1)