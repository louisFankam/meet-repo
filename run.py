#!/usr/bin/env python3
"""
Script de lancement de l'application Meet
"""

import os
import sys
from app import app, db
from sqlalchemy import text

def main():
    """Fonction principale de lancement"""
    print("🚀 Lancement de l'application Meet...")
    print("=" * 50)
    
    # Vérifier que la base de données existe
    try:
        with app.app_context():
            # Tester la connexion à la base de données
            db.session.execute(text('SELECT 1'))
            print("✅ Connexion à la base de données réussie")
            
            # Créer les tables si elles n'existent pas
            db.create_all()
            print("✅ Tables de la base de données vérifiées")
            
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        print("\n🔧 Solutions possibles:")
        print("1. Vérifiez que MySQL est démarré")
        print("2. Vérifiez la configuration dans config.py")
        print("3. Lancez d'abord: python database.py")
        print("\nExemple de configuration:")
        print("DATABASE_URL=mysql+pymysql://username:password@localhost/dating_app")
        return 1
    
    print("\n🌐 Démarrage du serveur web...")
    print("📱 L'application sera accessible à: http://localhost:5000")
    print("🛑 Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 50)
    
    try:
        # Lancer l'application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt de l'application Meet")
        return 0
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
