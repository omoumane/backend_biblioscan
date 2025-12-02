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

```text
backend_biblioscan/
│
├── ai_services/                 #  Services IA (Python)
│   ├── app.py                   # Point d'entrée IA
│   ├── models/                  # Modèles d'IA
│
├── htdocs/                      #  Backend PHP (API)
│   ├── bibliodb_api/            # Endpoints API
│   │   ├── config.php           # Configuration accès BD + IA
│
├── bibliodb.sql                 # 🗄️ Base de données MySQL
├── .gitignore
└── README.md
```

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

## Base de données : bibliodb
La base de données bibliodb stocke toutes les informations nécessaires au fonctionnement du système Biblioscan :
- gestion des utilisateurs
- gestion des bibliothèques de livres
- organisation spatiale des livres
- gestion des sessions d’authentification

Elle est composée de 4 tables principales :

---- users
```text
| Champ      | Type                 | Description                         |
| ---------- | -------------------- | ----------------------------------- |
| `user_id`  | int(11), PK, AI      | Identifiant unique de l’utilisateur |
| `username` | varchar(100), UNIQUE | Nom d’utilisateur (login)           |
| `password` | varchar(255)         | Mot de passe hashé (bcrypt)         |
| `nom`      | varchar(100)         | Nom de famille                      |
| `prenom`   | varchar(100)         | Prénom                              |
```
📌 Rôle
- Gestion des comptes
- Authentification
- Association des bibliothèques à un utilisateur (via bibliotheques.user_id)

---- user_tokens
```text
| Champ        | Type                        | Description                            |
| ------------ | --------------------------- | -------------------------------------- |
| `id`         | int(11), PK, AI             | Identifiant unique du token            |
| `user_id`    | int(11), FK → users.user_id | Utilisateur auquel appartient le token |
| `token`      | varchar(255), UNIQUE        | Token généré (sécurisé)                |
| `expires_at` | datetime                    | Date d’expiration                      |
```
📌 Rôle
- Stockage des tokens JWT-like ou personnalisés
- Système de session côté serveur
- Permet de vérifier si un utilisateur est connecté ou non

---- bibliotheques
```text
| Champ         | Type                        | Description                             |
| ------------- | --------------------------- | --------------------------------------- |
| `biblio_id`   | int(11), PK, AI             | Identifiant de la bibliothèque          |
| `user_id`     | int(11), FK → users.user_id | Propriétaire                            |
| `nom`         | varchar(100)                | Nom de la bibliothèque                  |
| `nb_lignes`   | int(11)                     | Nombre de lignes de l’étagère virtuelle |
| `nb_colonnes` | int(11)                     | Nombre de colonnes de l’étagère         |
```
📌 Rôle
- Chaque utilisateur peut avoir plusieurs bibliothèques.
- La position des livres est organisée en grille ligne/colonne, ce qui permet d’afficher une bibliothèque sous forme visuelle.

---- livres
```text
| Champ                 | Type                                  | Description                                               |
| --------------------- | ------------------------------------- | --------------------------------------------------------- |
| `livre_id`            | int(11), PK, AI                       | Identifiant du livre                                      |
| `biblio_id`           | int(11), FK → bibliotheques.biblio_id | Bibliothèque d’origine                                    |
| `titre`               | varchar(255)                          | Titre du livre (OCR + correction automatique ou manuelle) |
| `auteur`              | varchar(150)                          | Auteur                                                    |
| `date_pub`            | varchar(50)                           | Année ou date de publication                              |
| `position_ligne`      | int(11)                               | Ligne dans la grille de la bibliothèque                   |
| `position_colonne`    | int(11)                               | Colonne dans la grille                                    |
| `couverture_url`      | text                                  | URL de la couverture (Google Books)                       |
| `correction_manuelle` | tinyint(1)                            | 0 = auto, 1 = corrigé par un humain                       |
| `isbn`                | varchar(32)                           | ISBN si trouvé                                            |
```
📌 Rôle
Cette table est le cœur du projet :
- Sauvegarde des livres détectés via vision (OCR)
- Correction automatique (IA Python)
- Correction manuelle (interface utilisateur)
- Organisation spatiale dans la bibliothèque (position_ligne / position_colonne)
- Enrichissement via API Google Books (couverture_url, isbn, ...)

## Relation entre les tables
```text
   users
     │ 1
     │
     │ N
 bibliotheques
     │ 1
     │
     │ N
   livres

 users
     │ 1
     │
     │ N
 user_tokens
```
## API/PHP
1-  Authentification : login.php

📌 Objectif

Cet endpoint permet à un utilisateur de se connecter avec son username et son mot de passe.
S’il est authentifié avec succès :

les anciens tokens de cet utilisateur sont supprimés,

un nouveau token est généré,

ce token est sauvegardé dans la table user_tokens,

le backend renvoie ce token + l’user_id.

📥 Requête

URL : /bibliodb_api/login.php - Méthode : POST - Format d’entrée : application/json - Format de sortie : application/json

🧠 Logique & requêtes SQL

Récupérer l’utilisateur :
```text
SELECT user_id, password
FROM users
WHERE username = ?;
```
Vérifier le mot de passe (en PHP avec password_verify) :
```text
password_verify($password_entré, $row['password'])
```
Créer un token si OK :
```text
INSERT INTO user_tokens (user_id, token, expires_at)
VALUES (?, ?, ?);
```
expires_at = date/heure actuelle + X heures/jours.

2-  Inscription utilisateur : register.php

📌 Objectif

Cet endpoint permet de créer un nouveau compte utilisateur.

- vérifie que tous les champs requis sont présents,

- vérifie que le username n’est pas déjà utilisé,

- hash le mot de passe (bcrypt),

- insère un nouvel utilisateur dans la table users,

- renvoie une réponse JSON indiquant le succès ou l’erreur.

📥 Requête

URL : /bibliodb_api/register.php - Méthode : POST - Input : JSON (application/json) - Output : JSON (application/json)

🧠 Logique & requêtes SQL

Lecture & nettoyage des données:
```text
$data = json_decode(file_get_contents("php://input"), true);
$username = trim($data["username"] ?? '');
$password = trim($data["password"] ?? '');
$nom      = trim($data["nom"] ?? '');
$prenom   = trim($data["prenom"] ?? '');
```
Hash du mot de passe
```text
$hashedPassword = password_hash($password, PASSWORD_DEFAULT);
```
Vérifier si le username existe déjà
```text
SELECT user_id
FROM users
WHERE username = ?;
```
Insérer le nouvel utilisateur
```text
INSERT INTO users (username, password, nom, prenom)
VALUES (?, ?, ?, ?);
```
