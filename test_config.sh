#!/bin/bash

# Script de test rapide pour vérifier la configuration
echo "🔍 TEST DE CONFIGURATION RAPIDE"

# Vérifier si nous sommes dans le bon répertoire
if [ ! -f "app.py" ]; then
    echo "❌ app.py non trouvé. Êtes-vous dans le bon répertoire ?"
    exit 1
fi

# Vérifier l'environnement virtuel
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Environnement virtuel non activé"
    echo "💡 Lancez: source venv/bin/activate"
    exit 1
else
    echo "✅ Environnement virtuel activé: $VIRTUAL_ENV"
fi

# Vérifier les dépendances principales
echo "📦 Vérification des dépendances..."
python3 -c "
import sys
try:
    import flask
    print('✅ Flask:', flask.__version__)
except ImportError:
    print('❌ Flask non installé')
    sys.exit(1)

try:
    import flask_login
    print('✅ Flask-Login installé')
except ImportError:
    print('❌ Flask-Login non installé')
    sys.exit(1)

try:
    import flask_limiter
    print('✅ Flask-Limiter installé')
except ImportError:
    print('❌ Flask-Limiter non installé')
    sys.exit(1)

try:
    import flask_session
    print('✅ Flask-Session installé')
except ImportError:
    print('❌ Flask-Session non installé')
    sys.exit(1)

try:
    import pymysql
    print('✅ PyMySQL installé')
except ImportError:
    print('❌ PyMySQL non installé')
    sys.exit(1)

print('🎉 Toutes les dépendances sont installées !')
"

if [ $? -ne 0 ]; then
    echo "💡 Installez les dépendances: pip install -r requirements.txt"
    exit 1
fi

# Vérifier les fichiers de configuration
echo "📁 Vérification des fichiers..."
files_required=("app.py" "config.py" "rate_limit_config.py" "requirements.txt" ".env")
for file in "${files_required[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file trouvé"
    else
        echo "❌ $file manquant"
    fi
done

# Vérifier les dossiers
echo "📂 Vérification des dossiers..."
mkdir -p logs static/uploads
echo "✅ Dossiers créés/vérifiés"

# Test d'import simple
echo "🧪 Test d'import Python..."
python3 -c "
try:
    from app import create_app
    print('✅ Import app.py réussi')
    from rate_limit_config import configure_rate_limiter
    print('✅ Import rate_limit_config réussi')
    print('🎉 Configuration Python valide !')
except Exception as e:
    print(f'❌ Erreur import: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 TEST TERMINÉ AVEC SUCCÈS !"
    echo ""
    echo "🚀 POUR LANCER L'APPLICATION :"
    echo "   python3 app.py"
    echo ""
    echo "🔧 POUR LA PRODUCTION :"
    echo "   gunicorn --workers 3 --bind 0.0.0.0:5001 app:create_app()"
else
    echo ""
    echo "❌ TEST ÉCHOUÉ - Corrigez les erreurs ci-dessus"
fi