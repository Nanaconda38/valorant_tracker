# Plan d'Implémentation : Valorant Local Tracker

Ce document sert de guide étape par étape pour le développement du Tracker local. L'accent est mis sur la robustesse, la modularité et l'isolation des données par mode de jeu.

---

## 🛠️ Phase 1 : La Fenêtre et la Stack de Base (Dashboard UI Shell)
**Objectif :** Créer l'interface web locale vide et s'assurer que le serveur tourne en arrière-plan avec un rafraîchissement dynamique.

*   **Étape 1.1 : Structure des fichiers**
    Créer l'arborescence du projet :
```text
    ├── app.py                 # Serveur principal (FastAPI ou Flask)
    ├── lockfile_scanner.py    # Gestion de la connexion locale Riot
    ├── api_client.py          # Requêtes API externes (HenrikDev)
    ├── database.py            # Gestion SQLite
    ├── templates/
    │   └── index.html         # Interface HTML unique (Tailwind CSS via CDN)
    └── static/
        └── js/app.js          # Logique WebSocket ou Polling pour l'UI
    ```

*   **Étape 1.2 : Le Serveur Web & UI**
    *   Mettre en place une application minimale (FastAPI ou Flask).
    *   Créer la page `index.html` avec deux sections principales vides sous forme de tableaux face à face : **Alliés** (Bleu) et **Ennemis** (Rouge).
    *   Ajouter un widget en haut de page pour le **Live RR Tracker** (Bilan Session).

*   **Étape 1.3 : Validation Phase 1**
    *   Lancer `app.py` et vérifier que la page s'affiche correctement sur `http://localhost:8000`.

---

## 🔑 Phase 2 : Le Scanner de Lockfile (Connexion Riot Locale)
**Objectif :** Détecter si Valorant est lancé, lire ses identifiants locaux et intercepter le mode de jeu actuel.

*   **Étape 2.1 : Lecture du Lockfile**
    *   Écrire un script Python qui cherche le fichier `lockfile` dans le répertoire d'installation de Riot Games (`AppData/Local/Riot Games/Riot Client/Config/lockfile`).
    *   Extraire : `Port`, `Password` (encodé en Base64), et le protocole (`https`).

*   **Étape 2.2 : Client HTTP Local Insecure**
    *   Configurer un client HTTP (via `requests` ou `httpx`) capable d'ignorer les certificats SSL auto-signés de Riot (`verify=False`).
    *   Tester une requête sur l'endpoint local `/presence/v3/presences` pour récupérer ton propre pseudo.

*   **Étape 2.3 : Détecteur de Gamemode & Phase**
    *   Créer une boucle en tâche de fond qui interroge l'API locale pour détecter le statut de la session.
    *   Extraire le `queueId` (mode actuel : `competitive`, `swiftplay`, etc.) et la phase (`PREGAME`, `CORE-GAME`, `MENUS`).

*   **Étape 2.4 : Validation Phase 2**
    *   Vérifier dans la console Python que le script affiche bien le mode de jeu dès que tu lances une file d'attente.

---

## 👥 Phase 3 : Flux Pre-Game (Sélection des Agents - Alliés)
**Objectif :** Récupérer les données de tes coéquipiers pendant la phase de draft et interroger l'API externe.

*   **Étape 3.1 : Capture des PUUIDs Alliés**
    *   Dès que la phase passe à `PREGAME`, interroger l'endpoint local `/pregame/v1/matches/{pregame_match_id}`.
    *   Extraire les PUUIDs des 4 autres joueurs de ton équipe.

*   **Étape 3.2 : Intégration de l'API Externe (HenrikDev)**
    *   Écrire les fonctions asynchrones pour interroger l'API HenrikDev avec le PUUID et le `queueId` détecté à la Phase 2.
    *   Récupérer pour chaque allié : Rang actuel, Peak Rank, et l'historique de ses 20 derniers matchs dans ce mode spécifique (KD moyen, HS %, ACS).

*   **Étape 3.3 : Affichage Dynamique**
    *   Pousser ces données vers l'interface. Le tableau "Alliés" doit se remplir automatiquement pendant la sélection des agents.

*   **Étape 3.4 : Validation Phase 3**
    *   Lancer une partie, aller en sélection des agents, et vérifier que les fiches de tes 4 alliés s'affichent instantanément sur ton second écran.

---

## 🎯 Phase 4 : Flux Core-Game (Ennemis) & Algorithmes Tactiques
**Objectif :** Compléter le lobby avec les adversaires dès le chargement et calculer les indicateurs avancés (Tracker Score).

*   **Étape 4.1 : Capture des PUUIDs Ennemis**
    *   Dès que la phase passe à `CORE-GAME`, interroger l'endpoint local `/core-game/v1/matches/{coregroup_match_id}`.
    *   Extraire les PUUIDs des 5 joueurs adverses. Envoyer les requêtes API externes pour obtenir leurs statistiques (filtrées par le mode en cours).

*   **Étape 4.2 : Implémentation du Tracker Score (0 - 1000)**
    *   Coder la fonction Python de normalisation selon la formule convenue :
        *   **Impact (400 pts) :** Pondération ACS et KD.
        *   **Létalité (200 pts) :** Pourcentage de HS.
        *   **Forme (250 pts) :** Win Rate récent.
        *   **Peak (150 pts) :** Écart entre Rang Actuel et Peak Rank.

*   **Étape 4.3 : Indicateurs Tactiques Avancés**
    *   **Détecteur de Prémades :** Comparer les `matchId` récents dans les historiques des joueurs pour grouper visuellement les duos/trios.
    *   **Spécialiste Map :** Calculer le Win Rate du joueur uniquement sur la map en cours de chargement.
    *   **Agressivité :** Extraire le ratio First Blood / First Death de l'historique.
    *   **Mental / Forme :** Attribuer le badge "Tilt Alert" (3 défaites d'affilée + baisse d'ACS) ou "On Fire".

*   **Étape 4.4 : Validation Phase 4**
    *   Vérifier au chargement du match que les 10 lignes du tableau sont complètes, avec les groupes de prémades identifiés et les Tracker Scores calculés.

---

## 📊 Phase 5 : Base SQLite & Session Tracker
**Objectif :** Archiver tes propres données en fin de match et gérer le widget de performance en direct.

*   **Étape 5.1 : Modèle SQLite**
    *   Initialiser une base de données `tracker.db` avec une table `my_matches` (id, date, gamemode, map, agent, win_loss, rr_change, acs, kd, hs_percent).

*   **Étape 5.2 : Enregistrement Post-Match & Calcul du Live RR**
    *   Détecter la phase `MENUS` après un match.
    *   Interroger l'endpoint local `/mmr/v1/user/{my_puuid}` pour obtenir le delta exact de Rank Rating (RR).
    *   Sauvegarder la ligne dans la base SQLite.

*   **Étape 5.3 : UI de Session**
    *   Mettre à jour le widget supérieur du dashboard : calculer le nombre de victoires/défaites de la session actuelle et afficher le total de RR gagné ou perdu depuis le lancement de l'application.

*   **Étape 5.4 : Validation Phase 5**
    *   Vérifier après une partie que la base SQLite s'est incrémentée et que le widget de session affiche ton bilan de la soirée.