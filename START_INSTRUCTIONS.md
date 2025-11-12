# 🚀 Instructions de démarrage

## ❌ Erreur rencontrée
```
ModuleNotFoundError: No module named 'flask_session'
```

Cette erreur se produit car vous n'utilisez pas l'environnement virtuel qui contient toutes les dépendances.

## ✅ Solutions correctes

### Option 1: Utiliser l'environnement virtuel (recommandé)
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Démarrer l'application
python3 run.py
```

### Option 2: Utiliser directement le Python de l'environnement virtuel
```bash
venv/bin/python3 run.py
```

### Option 3: Utiliser le script de démarrage rapide
```bash
./start.sh
```

### Option 4: Si vous voulez absolument utiliser app.py directement
```bash
source venv/bin/activate
python3 app.py
```

## 🔧 Pourquoi cette erreur ?

- `python3` (sans venv) = Python système SANS les dépendances
- `venv/bin/python3` = Python de l'environnement virtuel AVEC les dépendances
- Les dépendances sont installées dans `venv/lib/python3.13/site-packages/`

## 📋 Vérification

Pour vérifier que Flask-Session est bien installé :
```bash
source venv/bin/activate
pip list | grep -i session
```

Résultat attendu : `Flask-Session        0.8.0`

---
💡 **Utilisez toujours `./start.sh` pour démarrer simplement !**