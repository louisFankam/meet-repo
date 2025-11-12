# 🚨 INSTRUCTIONS CORRECTIVES POUR LE DÉPLOIEMENT

## Problème identifié
Vous essayez de lancer l'application en dehors de l'environnement virtuel Python.

## Solution immédiate

### 1. Activer l'environnement virtuel
```bash
# Sur votre serveur dans le répertoire /www/wwwroot/meet-repo
source venv/bin/activate
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Lancer l'application
```bash
python3 app.py
```

## Solution complète recommandée

### Étape 1 : Préparation du serveur
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python et dépendances
sudo apt install python3 python3-pip python3-venv python3-dev mysql-server nginx -y

# Installer les dépendances Python système
sudo apt install python3-pymysql python3-pillow -y
```

### Étape 2 : Configuration MySQL
```bash
# Sécuriser MySQL
sudo mysql_secure_installation

# Créer la base de données
sudo mysql -u root -p
```

```sql
CREATE DATABASE meet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'meet_user'@'localhost' IDENTIFIED BY 'VOTRE_MOT_DE_PASSE_FORT';
GRANT ALL PRIVILEGES ON meet_db.* TO 'meet_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Étape 3 : Configuration du projet
```bash
# Aller dans le répertoire du projet
cd /www/wwwroot/meet-repo

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env.production
cp .env.production.example .env.production
```

### Étape 4 : Configurer .env.production
```bash
nano .env.production
```

```env
SECRET_KEY=VOTRE_SECRET_KEY_TRES_LONGUE_ET_ALEATOIRE_128_CHARS_MINIMUM
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://meet_user:VOTRE_MOT_DE_PASSE_FORT@localhost:3306/meet_db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
MESSAGE_EXPIRY_HOURS=24
NOTIFICATION_EXPIRY_HOURS=48
PROFILES_PER_PAGE=12
```

### Étape 5 : Créer les dossiers nécessaires
```bash
mkdir -p logs
mkdir -p static/uploads
touch static/uploads/.gitkeep
```

### Étape 6 : Tester l'application
```bash
# Toujours dans l'environnement virtuel
source venv/bin/activate

# Lancer en test
python3 app.py
```

### Étape 7 : Déployer avec Gunicorn (production)
```bash
# Lancer avec Gunicorn (toujours dans le venv)
gunicorn --workers 3 --bind 0.0.0.0:5001 app:create_app()
```

### Étape 8 : Configuration du service Systemd
```bash
# Créer le fichier de service
sudo nano /etc/systemd/system/meet.service
```

```ini
[Unit]
Description=Meet Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/www/wwwroot/meet-repo
Environment=FLASK_ENV=production
EnvironmentFile=/www/wwwroot/meet-repo/.env.production
ExecStart=/www/wwwroot/meet-repo/venv/bin/gunicorn --workers 3 --bind unix:meet.sock -m 007 app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable meet
sudo systemctl start meet

# Vérifier le status
sudo systemctl status meet
```

### Étape 9 : Configuration Nginx
```bash
# Créer la configuration Nginx
sudo nano /etc/nginx/sites-available/meet
```

```nginx
server {
    listen 80;
    server_name votre_domaine.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/www/wwwroot/meet-repo/meet.sock;
    }
    
    location /static {
        alias /www/wwwroot/meet-repo/static;
        expires 1y;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/meet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Vérification finale

### Test de l'application
```bash
# Vérifier que l'application fonctionne
curl http://localhost

# Vérifier les logs
sudo journalctl -u meet -f
```

### URLs de test
- `http://votre_ip/` - Page d'accueil
- `http://votre_ip/register` - Inscription
- `http://votre_ip/login` - Connexion

## Debug rapide

Si vous avez encore des erreurs :
```bash
# 1. Vérifier l'environnement virtuel
which python3  # Doit pointer vers venv/bin/python3

# 2. Vérifier les dépendances
pip list | grep -i flask

# 3. Vérifier la base de données
mysql -u meet_user -p meet_db -e "SHOW TABLES;"

# 4. Vérifier les permissions
ls -la /www/wwwroot/meet-repo/
```

---
⚡ **IMPORTANT : Toujours activer l'environnement virtuel avant de lancer l'application !**