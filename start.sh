#!/bin/bash

# Script de démarrage rapide pour l'application Meet
echo "🚀 Démarrage de l'application Meet..."
echo "Base de données: mysql+pymysql://root:root@localhost:3306/meet_db"
echo ""

# Activer l'environnement virtuel et démarrer
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 run.py
else
    echo "❌ Environnement virtuel non trouvé. Lancez d'abord:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
fi