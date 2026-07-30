# Rapport Technique - Application MedAI (Projet Pneumonie)

## 1. Introduction et Objectif
MedAI est une application web médicale complète développée avec **Django** (Python) visant à assister les radiologues et médecins dans le diagnostic de la pneumonie. L'application intègre un modèle d'Intelligence Artificielle de Deep Learning capable d'analyser des radiographies thoraciques, ainsi qu'un système de gestion de patients (Dossier Médical Électronique) et un tableau de bord analytique avancé.

## 2. Architecture Technologique
* **Backend :** Python 3, Django (Framework MVC)
* **Intelligence Artificielle :** TensorFlow / Keras (Modèle CNN binaire)
* **Interprétabilité IA :** Grad-CAM (génération de cartes de chaleur avec Matplotlib/OpenCV)
* **Frontend :** HTML5, Vanilla JavaScript, TailwindCSS (via CDN pour un rendu rapide)
* **Visualisation de Données :** Chart.js (v4)
* **Génération de Rapports :** `xhtml2pdf` (côté serveur) et API d'impression native (côté client)
* **Base de Données :** SQLite (par défaut sous Django, extensible vers PostgreSQL)

## 3. Modèle de Données (Base de Données)
L'architecture de la base de données est centralisée autour de deux entités principales dans `models.py` :

### 3.1. Modèle `Patient`
Gère les informations démographiques et médicales complètes.
* **Données d'identité :** Nom, prénom, date de naissance, sexe, téléphone, adresse.
* **Données physiologiques :** Poids (kg), taille (cm), groupe sanguin.
* **Facteurs de risque & historique :** Statut tabagique, allergies, antécédents médicaux, notes du médecin.

### 3.2. Modèle `Radiographie`
Gère le workflow d'analyse d'images.
* **Relations :** Lié à un `Patient` via clé étrangère.
* **Fichiers :** Stockage de l'image originale (`image`) et de l'image Grad-CAM (`heatmap_image`).
* **Résultats IA :** `classe_predite` (Normal / Pneumonie), `pourcentage_confiance` (en %).
* **Validation humaine :** `validation_medecin` (Confirmé, Corrigé, En attente) permettant de ré-entraîner ou d'auditer l'IA ultérieurement.

## 4. Moteur d'Intelligence Artificielle
La logique d'inférence se trouve dans `utils.py`.
* **Chargement du modèle :** Le modèle `best_model.h5` est chargé une seule fois au démarrage de l'application via une variable globale pour éviter les latences de chargement (Warm-start).
* **Inférence :** L'image brute est passée au modèle. L'architecture interne du modèle gère le redimensionnement et la normalisation (grâce aux couches `InputLayer` et `Rescaling`). La sortie utilise une fonction d'activation Sigmoïde où une probabilité `> 0.5` indique un poumon **Normal**, et `<= 0.5` indique une **Pneumonie**.
* **Grad-CAM :** Utilisation de `tf.GradientTape` pour extraire les gradients de la dernière couche convolutive. La carte de chaleur est ensuite fusionnée avec l'image originale via `matplotlib` et `cv2` pour expliquer visuellement au médecin les zones du poumon ayant conduit au diagnostic.

## 5. Interface Utilisateur (Design System)
L'application arbore un design ultra-moderne basé sur le style **Glassmorphism**.
* **Palette de couleurs :** Utilisation d'un dégradé doux (`surface` vers `secondary-container`), des couleurs sémantiques strictes (Primaire = Bleu médical, Erreur = Rouge, Succès = Vert).
* **Composants :** Panneaux translucides (`backdrop-blur-xl`, `bg-white/70`), bordures blanches subtiles et ombres légères pour créer une sensation de profondeur et de hiérarchie visuelle.
* **Typographie :** Utilisation stricte de la police **Inter** (Google Fonts).

## 6. Fonctionnalités Clés et Pages

### 6.1. Tableau de bord (Dashboard)
Aperçu immédiat des dernières analyses en attente et des statistiques globales (Analyses totales, Patients totaux).

### 6.2. Gestion des Patients & Téléexpertise
* Ajout de patients avec des formulaires riches et responsifs (`ajouter_patient.html`).
* Fiche détaillée du patient (`patient_detail.html`) permettant de voir l'historique complet de ses radiographies.
* Génération d'un **Rapport PDF** officiel et téléchargeable pour chaque diagnostic.

### 6.3. Tableau de Bord Analytique (`statistics.html`)
Une vue complète pour le pilotage de l'activité du service de radiologie :
* **KPIs :** Volume d'analyses, taux de pneumonie, confiance moyenne de l'IA.
* **Tendance Diagnostique Dynamique :** Un graphique Chart.js (Area Chart) permettant de filtrer les résultats sur 7 jours, 30 jours, ou 6 mois sans rechargement de page (JavaScript Vanilla).
* **Analyses Démographiques :** Répartition par Sexe, Statut tabagique, Groupes sanguins et validation IA sous forme de graphiques *Donut* et *Bar*.
* **Export PDF :** Optimisation CSS (`@media print`) masquant l'interface de navigation pour exporter le tableau de bord en rapport PDF clair.

### 6.4. Paramètres & Notifications Push (`settings.html`)
* Modification des données du médecin et de son mot de passe.
* **Notifications Web natives :** Intégration de l'API de notifications des navigateurs. Le médecin peut activer les alertes (enregistrées via `localStorage`) pour recevoir des pop-ups de son système d'exploitation lors de l'obtention de résultats critiques.

## 7. Sécurité & Bonnes Pratiques
* **Authentification :** Toutes les vues (`views.py`) sont protégées par le décorateur `@login_required`.
* **Protection CSRF :** Tous les formulaires incluent `{% csrf_token %}`.
* **Optimisation :** Pas d'appels répétés coûteux. Les statistiques sont traitées via les fonctions d'agrégation de Django (`Count`, `Avg`, `TruncMonth`, `TruncDay`) pour minimiser le coût des requêtes SQL.

## 8. Commandes Utiles
Lancer l'application :
```bash
python manage.py runserver
```

Mettre à jour la base de données :
```bash
python manage.py makemigrations
python manage.py migrate
```

Pusher le code sur Git :
```bash
git add .
git commit -m "Mise à jour du projet"
git push origin main
```
