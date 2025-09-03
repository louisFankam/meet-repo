# 💕 Meet - Application de Rencontre

Une application de rencontre moderne et gratuite construite avec Flask, Tailwind CSS et SQLite, offrant une expérience utilisateur fluide et intuitive.

## 🌟 Fonctionnalités

### ✨ **Fonctionnalités principales**
- **Matching intelligent** : Découverte de profils basée sur les centres d'intérêt
- **Messages éphémères** : Conversations qui disparaissent après 24h
- **Interface responsive** : Design mobile-first qui s'adapte à tous les appareils
- **Géolocalisation** : Filtrage par ville et proximité
- **100% gratuit** : Aucun abonnement, aucune limitation

### 🔐 **Authentification et sécurité**
- Inscription/connexion sécurisées
- Gestion des sessions avec Flask-Login
- Mots de passe hashés avec bcrypt
- Protection CSRF

### 📱 **Interface utilisateur**
- Design moderne avec Tailwind CSS
- Navigation mobile avec menu hamburger
- Modals interactifs pour les profils et matches
- Pagination des résultats
- Filtres avancés (âge, ville, centres d'intérêt)

### 🧹 **Maintenance automatique**
- Nettoyage automatique des données expirées
- Suppression des messages et notifications obsolètes
- Planification des tâches avec APScheduler

### 👨‍💼 **Administration**
- Interface d'administration complète
- Statistiques en temps réel
- Export des données
- Gestion des utilisateurs

## 🛠️ Technologies utilisées

### **Backend**
- **Flask** : Framework web Python
- **SQLAlchemy** : ORM pour la base de données
- **Flask-Login** : Gestion de l'authentification
- **Flask-WTF** : Validation des formulaires
- **APScheduler** : Planification des tâches
- **bcrypt** : Hachage sécurisé des mots de passe

### **Frontend**
- **HTML5** : Structure sémantique
- **Tailwind CSS** : Framework CSS utilitaire
- **JavaScript** : Interactions dynamiques
- **Jinja2** : Moteur de templates

### **Base de données**
- **SQLite** : Base de données légère et portable
- **MySQL** : Support pour la production

## 🚀 Installation et configuration

### **Prérequis**
- Python 3.8+
- pip
- Git

### **Installation**

1. **Cloner le repository**
   ```bash
   git clone https://github.com/louisFankam/meet-repo.git
   cd meet-repo
   ```

2. **Créer un environnement virtuel**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**
   ```bash
   # Copier le fichier de configuration
   cp .env.example .env
   # Éditer les variables d'environnement
   nano .env
   ```

5. **Initialiser la base de données**
   ```bash
   python app.py
   ```

6. **Lancer l'application**
   ```bash
   python app.py
   ```

L'application sera accessible à l'adresse : `http://localhost:5000`

## 📁 Structure du projet

```
meet-repo/
├── app.py                 # Application principale Flask
├── config.py             # Configuration de l'application
├── requirements.txt      # Dépendances Python
├── README.md            # Documentation du projet
├── .gitignore           # Fichiers à ignorer par Git
├── static/              # Fichiers statiques
│   ├── css/            # Styles CSS
│   ├── js/             # JavaScript
│   └── uploads/        # Photos des utilisateurs
├── templates/           # Templates HTML
│   ├── base.html       # Template de base
│   ├── dashboard.html  # Tableau de bord
│   ├── profile.html    # Profil utilisateur
│   ├── messages.html   # Messages
│   ├── matches.html    # Matches
│   └── admin.html      # Interface d'administration
└── venv/               # Environnement virtuel Python
```

## 🎯 Utilisation

### **Première utilisation**
1. Créez un compte avec votre email
2. Complétez votre profil (photos, bio, centres d'intérêt)
3. Découvrez des profils qui correspondent à vos critères
4. Likez les profils qui vous intéressent
5. Attendez les matches mutuels pour commencer à discuter

### **Fonctionnalités avancées**
- **Filtres** : Affinez vos recherches par âge, ville et centres d'intérêt
- **Géolocalisation** : Découvrez des personnes près de chez vous
- **Notifications** : Restez informé des nouveaux matches et messages
- **Administration** : Accédez aux statistiques et outils de gestion

## 🔧 Configuration avancée

### **Variables d'environnement**
```bash
SECRET_KEY=votre-clé-secrète-ici
DATABASE_URL=sqlite:///meet.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
MESSAGE_EXPIRY_HOURS=24
NOTIFICATION_EXPIRY_HOURS=48
PROFILES_PER_PAGE=12
```

### **Base de données MySQL**
Pour utiliser MySQL en production :
```bash
DATABASE_URL=mysql+pymysql://user:password@localhost/meet_db
```

## 📊 Statistiques et monitoring

L'interface d'administration fournit :
- Nombre total d'utilisateurs
- Statistiques des matches
- Messages échangés
- Conversations actives
- Utilisateurs récents

## 🚀 Déploiement

### **Déploiement local**
```bash
python app.py
```

### **Déploiement en production**
```bash
# Avec Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Avec Docker
docker build -t meet-app .
docker run -p 8000:8000 meet-app
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation
- Contactez l'équipe de développement

## 🎉 Remerciements

- **Flask** pour le framework web robuste
- **Tailwind CSS** pour le design moderne
- **SQLAlchemy** pour l'ORM puissant
- **La communauté open source** pour les outils et bibliothèques

---

**Développé avec ❤️ par louisFankam**

*Une application de rencontre moderne, gratuite et open source*
