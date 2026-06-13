# 📌 Feuille de Route : Valorant Local Tracker (Phase 1)

> [!IMPORTANT]
> **CONSIGNES POUR L'ASSISTANT IA :**
> - Ce fichier sert de point d'ancrage pour le développement. À chaque nouvelle session ou étape, lis attentivement cette feuille de route pour savoir où en est le projet.
> - Mets à jour le statut des tâches en remplaçant `[ ]` par `[/]` lorsqu'une tâche est en cours, et par `[x]` lorsqu'elle est terminée avec succès.
> - Si tu t'arrêtes au milieu d'une tâche, note brièvement l'état actuel ou les difficultés rencontrées en dessous de la tâche pour faciliter la reprise.
> - Ne passe à la phase suivante du plan global que lorsque toutes les tâches de la phase en cours sont marquées `[x]` et validées.

---

## 🗺️ Avancement de la Phase 1

- `[x]` **Configuration initiale et structure des fichiers**
  - `[x]` Créer et activer l'environnement virtuel Python
  - `[x]` Installer les dépendances de base (`fastapi`, `uvicorn`, `jinja2`) et générer `requirements.txt`
  - `[x]` Créer le fichier serveur principal : `app.py`
  - `[x]` Créer le squelette de détection locale : `lockfile_scanner.py`
  - `[x]` Créer le squelette de client API externe : `api_client.py`
  - `[x]` Créer le squelette de base de données : `database.py`
  - `[x]` Créer les dossiers de templates et statiques : `templates/` et `static/`
  - `[x]` Créer les fichiers de l'UI : `templates/index.html`, `static/css/style.css` et `static/js/app.js`

- `[x]` **Développement du Serveur FastAPI (`app.py`)**
  - `[x]` Importer FastAPI et configurer le montage des fichiers statiques (`/static`) et le moteur de templates Jinja2
  - `[x]` Créer la route d'accueil `/` qui sert `index.html`
  - `[x]` Créer une route API fictive `/api/session-status` renvoyant le statut actuel du tracker (ex. `{"status": "searching_game"}`)

- `[x]` **Création de la Maquette Dynamique (Dashboard UI Shell)**
  - `[x]` Définir les variables de couleur (palette premium sombre, rouge Valorant `#ff4655`, bleu `#00ea9a`/`#00f0ff`) et la typographie (fonts *Outfit* et *Inter*) dans `style.css`
  - `[x]` Créer l'en-tête du Dashboard contenant le widget **Live RR Tracker** (Bilan de session : Win/Loss, points gagnés/perdus)
  - `[x]` Structurer la zone principale avec deux colonnes face à face : **Alliés** (accent bleu) et **Ennemis** (accent rouge)
  - `[x]` Ajouter des cartes de joueurs factices (placeholders) avec statistiques (Rang, KD, HS%, ACS) et badges (ex. "On Fire", "Tilt Alert") pour tester le rendu visuel
  - `[x]` S'assurer que le design est entièrement responsive et adapté pour un affichage sur un second écran

- `[x]` **Logique UI et Communication Client-Serveur (`app.js`)**
  - `[x]` Écrire un script pour interroger périodiquement `/api/session-status` (polling) ou établir une connexion WebSocket
  - `[x]` Mettre en valeur l'état de connexion de manière dynamique dans l'UI (pastille de statut : Rouge = Hors-ligne, Vert = Connecté au jeu)

- `[x]` **Vérification et Recette Phase 1**
  - `[x]` Lancer le serveur avec la commande `python -m uvicorn app:app --reload`
  - `[x]` Vérifier le rendu sur `http://localhost:8000` et s'assurer de l'absence d'erreurs console

---

## 🔑 Avancement de la Phase 2 : Le Scanner de Lockfile & Connexion Riot Locale

- `[x]` **Détecteur de Lockfile (`lockfile_scanner.py`)**
  - `[x]` Importer `os` et `base64`
  - `[x]` Rechercher le fichier lockfile dans `%LOCALAPPDATA%/Riot Games/Riot Client/Config/lockfile`
  - `[x]` Lire et parser le port, le mot de passe et le protocole
  - `[x]` Encoder en Base64 les identifiants pour l'authentification LCU

- `[x]` **Boucle de Tâche en Arrière-plan (`app.py`)**
  - `[x]` Initialiser un loop asynchrone lors du startup de FastAPI
  - `[x]` Requêter `/chat/v1/session` pour récupérer le PUUID et le pseudo du joueur local
  - `[x]` Requêter `/chat/v4/presences` pour identifier la phase active du jeu (`MENUS`, `PREGAME`, `CORE-GAME`) et le queue ID
  - `[x]` Exposer ces détails dans l'endpoint `/api/session-status`

- `[x]` **Mise à Jour de l'Interface (`app.js`)**
  - `[x]` Modifier le script client pour analyser le payload d'état enrichi
  - `[x]` Afficher le statut actuel (`VALORANT: MENUS`, `VALORANT: PRE-GAME` etc.) dynamiquement

- `[x]` **Recette et Validation Phase 2**
  - `[x]` Lancer le serveur via WSL
  - `[x]` Vérifier la mise à jour dynamique du widget de statut dans le dashboard

---

## 👥 Avancement de la Phase 3 : Flux Pre-Game (Sélection des Agents - Alliés)

- `[x]` **Capture des PUUIDs Alliés**
  - `[x]` Interroger l'endpoint GLZ `/pregame/v1/players/{puuid}` pour récupérer le MatchID de draft
  - `[x]` Extraire les PUUIDs des alliés via `/pregame/v1/matches/{pregame_match_id}`
  - `[x]` Résoudre les pseudos via le service PD Name Service `/name-service/v2/players`

- `[x]` **Intégration de l'API HenrikDev**
  - `[x]` Créer la classe `HenrikDevClient` avec un système de cache
  - `[x]` Requêter les statistiques (Rang, Peak Rank, KD, HS%, ACS) pour chaque PUUID
  - `[x]` Mettre en place un fallback sur données fictives (mock stats) si aucune clé API n'est fournie

- `[x]` **Affichage Dynamique Alliés**
  - `[x]` Pousser les données des coéquipiers vers le frontend pendant la draft
  - `[x]` Masquer les ennemis durant la phase de sélection pour respecter les règles du jeu

- `[x]` **Recette et Validation Phase 3**
  - `[x]` Entrer en sélection des agents et vérifier le rendu dynamique des cartes alliées

---

## 🎯 Avancement de la Phase 4 : Flux Core-Game (Ennemis) & Algorithmes Tactiques

- `[x]` **Capture des PUUIDs Ennemis**
  - `[x]` Détecter le passage en phase `CORE-GAME`
  - `[x]` Interroger GLZ `/core-game/v1/players/{puuid}` pour obtenir le MatchID de match en direct
  - `[x]` Extraire les PUUIDs des 10 joueurs du match via `/core-game/v1/matches/{match_id}`
  - `[x]` Résoudre tous les pseudos et taglines à l'aide de l'API PD Name Service

- `[x]` **Implémentation du Tracker Score**
  - `[x]` Coder la fonction de score sur 1000 points combinant ACS, KD, HS%, et l'écart de rang actuel/peak
  - `[x]` Formater l'affichage avec des classes CSS de couleur dynamiques (`score-excellent`, `score-good`, etc.)

- `[x]` **Algorithmes Tactiques & Badges**
  - `[x]` Détecteur de groupes prémades (comparaison d'historiques récents)
  - `[x]` Associer des badges de premades colorés (`premade-group-1` à `5`) aux duos/trios identifiés
  - `[x]` Afficher le badge individuel ("On Fire", "Tilt Alert", "Smurf Alert") issu des données de performance

- `[x]` **Rendu Frontend Double Colonne**
  - `[x]` Mettre à jour `app.js` pour appeler `renderPlayerList` sur les alliés et les ennemis en même temps
  - `[x]` Implémenter des états intermédiaires de chargement et d'attente (Practice Range, Menus, Draft)
  - `[x]` Assurer la restauration des fiches mockups originales si le client passe hors-ligne

- `[x]` **Recette et Validation Phase 4**
  - `[x]` Rejoindre un match en direct (ex. Team Deathmatch) et valider le chargement complet des 10 joueurs, du score tracker et des premades dans le dashboard

---

## 📊 Avancement de la Phase 5 : Base SQLite & Session Tracker

- `[x]` **Modèle SQLite**
  - `[x]` Initialiser `tracker.db`
  - `[x]` Créer la table `my_matches` avec les champs post-match principaux
  - `[x]` Empêcher les doublons via `match_id`

- `[x]` **Enregistrement Post-Match & RR**
  - `[x]` Réutiliser le résumé post-game après retour `MENUS`
  - `[x]` Récupérer le delta RR via les endpoints MMR Riot disponibles
  - `[x]` Sauvegarder la ligne de match dans SQLite

- `[x]` **UI de Session**
  - `[x]` Exposer `session_summary` dans `/api/session-status`
  - `[x]` Mettre à jour le widget haut de page avec wins/losses/RR depuis la session serveur
  - `[x]` Afficher le RR sur la carte post-match

- `[/]` **Recette et Validation Phase 5**
  - `[x]` Valider le modèle SQLite sur base temporaire
  - `[x]` Valider le parsing RR sur payloads Riot
  - `[x]` Valider l'affichage du widget et de la carte post-match dans Chrome visible avec données simulées
  - `[/]` Confirmer après une vraie partie que `tracker.db` s'incrémente et que le RR correspond au client
