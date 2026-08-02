# 🫁 MedAI — Plateforme d'Analyse Radiographique et Facturation

MedAI est une application médicale moderne conçue pour assister les radiologues et pneumologues dans la détection de la pneumonie à l'aide de l'Intelligence Artificielle. Elle intègre également un module de gestion des dossiers patients, de statistiques cliniques et de facturation (Finance).

---

## ✨ Fonctionnalités Principales

### 🩺 Module Médical & IA
- **Dossiers Patients complets** : Informations cliniques (antécédents, groupe sanguin, statut fumeur, etc.).
- **Analyse d'images radiographiques (IA)** : Prédiction instantanée de la pneumonie via le modèle `EfficientNet` (Keras/TensorFlow).
- **Exécution Asynchrone (Background)** : L'IA tourne en arrière-plan (via Threads), libérant instantanément l'interface avec un système de polling AJAX.
- **Grad-CAM (Heatmap)** : Génération automatique de cartes de chaleur pour visualiser les zones d'intérêt identifiées par l'IA.
- **Validation Médicale** : Les médecins peuvent confirmer ou corriger les diagnostics suggérés par l'IA.

### 💰 Module Finance (Comptabilité)
- **Facturation automatique** liée aux actes de radiologie.
- **Gestion des tarifs et paiements** (en attente, partiels, payés).
- **Génération de Factures PDF professionnelles** comprenant :
  - Profil du médecin émetteur (INPE, spécialité, adresse).
  - Détail du patient et de la radiographie analysée.
  - Historique complet des paiements reçus.
- **Rapports PDF médicaux** prêts à l'impression.

---

## 🛠️ Design System & Ergonomie

L'application utilise le design system **Clinical Precision** basé sur Tailwind CSS :
- **Aesthétiques épurées et professionnelles** adaptées à l'environnement clinique.
- **Palette de couleurs optimisée** (Bleus médicaux, statuts clairs avec *Emerald* pour Normal et *Rose* pour Pneumonie).
- **Typographie lisible (Inter)** optimisée pour les données numériques et tabulaires.
- **Favicon et logo intégrés** à l'ensemble du site et des PDF.

---

## 🚀 Installation et Lancement local

### Prérequis
- Python 3.10+
- MySQL (via XAMPP ou installation propre)

### Étape 1 : Configurer la base de données
1. Démarrez **MySQL** (ex: via XAMPP).
2. Créez une base de données vide nommée : `pneumonie_db` (en `utf8mb4_general_ci`).

### Étape 2 : Configuration locale (`.env`)
Créez ou modifiez le fichier `.env` à la racine du projet :
```env
SECRET_KEY=django-insecure-votre-cle-secrete
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=django.db.backends.mysql
DB_NAME=pneumonie_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Étape 3 : Commandes d'installation
Exécutez les commandes suivantes dans votre terminal :

```bash
# 1. Activer l'environnement virtuel
source venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Appliquer les migrations de base de données
python manage.py migrate

# 4. Charger les données d'exemples (Tarifs & Factures)
python manage.py seed_tarifs
python manage.py seed_factures

# 5. Lancer le serveur de développement
python manage.py runserver
```

Rendez-vous ensuite sur 👉 **`http://127.0.0.1:8000/`**

---

## 🛡️ Sécurité des données de santé
- **Média Protégés** : Toutes les images de radiographies (`/media/`) sont protégées et accessibles uniquement par authentification (les URLs directes ne sont pas publiques).
- **Gestion des rôles** : Cloisonnement strict des accès entre le personnel médical (Médecins) et administratif (Comptables).
