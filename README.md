# 📚 backend_biblioscan

Backend du projet **BiblioScan** : une plateforme permettant de gérer et d’analyser des documents de bibliothèque (scan, extraction, recherche, etc.).

Ce dépôt contient :
- Un backend applicatif (PHP, dossier `htdocs/`).
- Des services d’intelligence artificielle (Python, dossier `ai_services/`).

## 🧩 Fonctionnalités principales

- Gestion des utilisateurs (inscription, connexion, authentification).
- Gestion des bibliothèques (Ajout, Suppression, liste).
- Gestion des livres (Ajout, Modification, Suppression, recherche, liste).
- Analyse des documents via des services d’IA :
  - <exemple : OCR, extraction de texte, résumé, classification, etc.>
- API REST pour interaction avec un frontend ou des clients externes.

## 🏗️ Architecture générale

backend_biblioscan/
│
├── ai_services/ # 🤖 Services IA (Python)
│ ├── app.py # Point d'entrée IA
│ ├── models/ # Modèles d'IA
│ └── utils/ # Scripts utilitaires
│
├── htdocs/ # 🧩 Backend PHP (API)
│ ├── bibliodb_api/ # Endpoints API
│ │ ├── config.php # Configuration accès BD + IA
│ │ ├── *.php # Scripts API
│ ├── index.php # Page d'entrée
│
├── bibliodb.sql # 🗄️ Base de données MySQL
├── .gitignore
└── README.md

## Comment lancer le serveur
1- Démarrer le serveur XAMPP (Apache + MySQL)
Ouvrir XAMPP Control Panel.
  Démarrer les modules :
    ✔ Apache
    ✔ MySQL
Les fichiers du backend doivent etre placés dans : C:/xampp/htdocs/biblidb_api/
2- Lancer les AI Services (Python)
Les fichiers du AI_Services etre placés dans : C:/xampp/ai_services
Dans un terminal :
    cd C:\xampp\ai_services
    venv\Scripts\activate
  // On devra voir : (venv) C:\xampp\ai_services>
    uvicorn app:app --host 127.0.0.1 --port 8000 --root-path /ai
3- Lanche ngrok sur le port Ngrok:
ngrok http --url=fancy-dog-formally.ngrok-free.app 80

    


