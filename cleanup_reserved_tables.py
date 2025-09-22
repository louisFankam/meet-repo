#!/usr/bin/env python3
"""
Script pour nettoyer les anciennes tables avec noms réservés SQL
"""

import pymysql
import sys

def cleanup_old_tables():
    """Supprime les anciennes tables si elles existent"""
    
    try:
        # Connexion à la base de données
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='meet_db'
        )
        
        with connection.cursor() as cursor:
            # Vérifier si la table 'like' existe
            cursor.execute("SHOW TABLES LIKE 'like'")
            result = cursor.fetchone()
            
            if result:
                print("Suppression de l'ancienne table 'like'...")
                cursor.execute("DROP TABLE IF EXISTS `like`")
                print("✅ Table 'like' supprimée")
            else:
                print("ℹ️  L'ancienne table 'like' n'existe pas")
            
            # Vérifier si la table 'match' existe
            cursor.execute("SHOW TABLES LIKE 'match'")
            result = cursor.fetchone()
            
            if result:
                print("Suppression de l'ancienne table 'match'...")
                cursor.execute("DROP TABLE IF EXISTS `match`")
                print("✅ Table 'match' supprimée")
            else:
                print("ℹ️  L'ancienne table 'match' n'existe pas")
        
        connection.commit()
        print("\n🎉 Nettoyage terminé!")
        print("Les tables avec noms réservés SQL ont été nettoyées.")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == "__main__":
    print("Nettoyage des anciennes tables avec noms réservés SQL...")
    success = cleanup_old_tables()
    
    if success:
        print("✅ Nettoyage réussi!")
    else:
        print("❌ Échec du nettoyage!")
        sys.exit(1)