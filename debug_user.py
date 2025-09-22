#!/usr/bin/env python3
"""
Vérifier l'utilisateur de test
"""

import sys
sys.path.insert(0, '.')

from model.database import db
from model.models import User
from app import create_app

app = create_app()

with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    if user:
        print(f"Utilisateur trouvé:")
        print(f"Email: {user.email}")
        print(f"Nom: {user.full_name}")
        print(f"Actif: {user.is_active}")
        print(f"Mot de passe (hash): {user.password_hash[:50]}...")
        
        # Tester la vérification du mot de passe
        print(f"\nTest mot de passe 'password123': {user.check_password('password123')}")
        print(f"Test mot de passe 'wrong': {user.check_password('wrong')}")
    else:
        print("Utilisateur non trouvé!")