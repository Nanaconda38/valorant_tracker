# Valorant Tracker Desktop App - Specifications

## 1. Objectif

Transformer le tracker local actuel en application Windows distribuable a des amis via un installer `.exe`.

L'application doit rester locale, simple a installer, et utilisable par un joueur non technique. Elle doit permettre de suivre les matchs Valorant, calculer les scores de performance, afficher les adversaires/allies pendant les phases de jeu, et conserver une carriere locale par utilisateur.

## 2. Public cible

- Joueurs Valorant Windows.
- Utilisateurs non developpeurs.
- Premier cercle de test : amis du createur.
- Distribution initiale privee, sans backend central.

## 3. Principe produit

L'application est un outil local :

- aucune base de donnees partagee entre utilisateurs ;
- aucune synchronisation cloud ;
- aucune collecte centralisee ;
- chaque installation gere ses donnees, sa cle API et son historique ;
- l'application lit le client Riot local via le lockfile quand Valorant est lance ;
- l'application utilise HenrikDev API pour enrichir les profils joueurs.

## 4. Choix d'architecture recommande

### Option recommandee pour la V1 : Python + FastAPI + pywebview

Le projet actuel est deja une application FastAPI avec frontend HTML/CSS/JS. Le chemin le plus leger est donc :

- garder FastAPI comme backend local ;
- lancer le serveur local en arriere-plan sur `127.0.0.1` avec un port libre ;
- ouvrir une vraie fenetre native via `pywebview`, basee sur Microsoft Edge WebView2 ;
- empaqueter le tout avec PyInstaller ;
- creer un installer Windows avec Inno Setup ou NSIS.

Avantages :

- beaucoup plus leger qu'Electron ;
- reutilise presque tout le code actuel ;
- donne une vraie fenetre d'application, pas un onglet navigateur ;
- compatible Windows moderne grace a WebView2 ;
- packaging Python relativement direct.

Limites :

- rendu dependant de WebView2 installe sur Windows ;
- moins flexible qu'Electron pour certaines integrations desktop avancees ;
- il faudra gerer proprement le cycle de vie backend/fenetre.

### Alternative : Electron

Electron est possible et confortable, comme Discord, mais plus lourd.

Avantages :

- ecosysteme tres mature ;
- packaging et auto-update tres documentes ;
- UI Chromium controlee.

Inconvenients :

- poids disque/RAM nettement superieur ;
- integration Python backend plus complexe ;
- risque de surarchitecture pour une V1 locale.

### Alternative : Tauri

Tauri est plus leger qu'Electron, mais demande Rust et une integration plus soigneuse avec le backend Python.

Conclusion V1 : partir sur `pywebview + PyInstaller + Inno Setup`. Reevaluer Electron/Tauri seulement si pywebview bloque.

## 5. Installation utilisateur

### Parcours installeur

1. L'utilisateur lance `ValorantTrackerSetup.exe`.
2. L'installeur installe l'application dans `%LOCALAPPDATA%\ValorantTracker` ou `Program Files` selon le mode choisi.
3. L'installeur cree :
   - un raccourci Bureau ;
   - un raccourci Menu Demarrer ;
   - un dossier de donnees utilisateur dans `%APPDATA%\ValorantTracker`.
4. Au premier lancement, l'application ouvre un ecran d'onboarding.

### Onboarding cle HenrikDev

Au premier lancement, l'utilisateur doit renseigner sa cle API HenrikDev.

L'ecran doit presenter 3 ou 4 etapes simples :

1. Aller sur le site HenrikDev / dashboard API.
2. Se connecter ou creer un compte.
3. Generer une cle API Valorant.
4. Copier la cle et la coller dans le champ affiche dans l'application.

UI attendue :

- un titre clair : `Configuration HenrikDev API`;
- un court texte expliquant pourquoi la cle est necessaire ;
- un bouton/lien `Ouvrir HenrikDev`;
- une liste d'etapes numerotees ;
- un champ texte ou password pour coller la cle ;
- un bouton `Verifier et sauvegarder`;
- un message d'erreur si la cle est invalide ou si l'API ne repond pas ;
- un bouton `Continuer sans cle` optionnel, mais l'app doit prevenir que les stats adversaires seront limitees.

La cle doit etre testee avant sauvegarde via un appel API simple HenrikDev.

## 6. Stockage local

### Emplacement des donnees

Les donnees runtime ne doivent pas rester dans le dossier d'installation. Elles doivent etre dans :

`%APPDATA%\ValorantTracker`

Contenu attendu :

- `tracker.db` : base SQLite locale ;
- `config.json` ou `settings.json` : preferences non sensibles ;
- `logs/` : logs applicatifs ;
- `cache/` : caches API et assets dynamiques si necessaire.

### Cle API

La cle HenrikDev ne doit pas etre stockee en clair dans le repo ni dans un `.env` distribue.

V1 acceptable :

- stockage via Windows Credential Manager si faisable rapidement ;
- sinon stockage chiffre avec DPAPI Windows via une librairie Python adaptee.

Fallback temporaire possible pour prototype :

- `config.json` local avec permission utilisateur uniquement.

Ce fallback doit etre marque comme temporaire.

## 7. Base de donnees

Chaque utilisateur a sa propre base SQLite locale.

Contraintes :

- aucune communication entre bases ;
- aucune dependance serveur ;
- migrations automatiques au lancement ;
- backup simple possible en copiant `%APPDATA%\ValorantTracker\tracker.db`.

Tables existantes a conserver/etendre :

- matchs sauvegardes ;
- cache details match Riot ;
- configuration locale si on decide de la mettre en DB ;
- eventuellement cache profils HenrikDev.

La DB doit etre creee automatiquement si elle n'existe pas.

## 8. Fonctionnement applicatif

### Demarrage

Au lancement :

1. charger la config locale ;
2. verifier si la cle HenrikDev existe ;
3. si aucune cle : afficher onboarding ;
4. initialiser la DB locale ;
5. lancer le backend FastAPI sur `127.0.0.1` avec un port disponible ;
6. ouvrir la fenetre native ;
7. demarrer le polling Riot local.

### Detection Valorant

L'application continue d'utiliser le lockfile Riot :

- si Valorant est ferme : afficher etat offline ;
- si Valorant est ouvert : lire phase, map, queue, joueurs ;
- pendant pregame/core-game : charger allies/adversaires ;
- post-match : recuperer `match-details`, sauvegarder le match, extraire `seasonId`.

### Gestion des erreurs

Cas a gerer :

- Valorant ferme ;
- lockfile introuvable ;
- API HenrikDev absente ou cle invalide ;
- rate-limit HenrikDev ;
- Riot local temporairement indisponible ;
- match-details indisponible juste apres la fin du match ;
- port local deja utilise ;
- DB verrouillee ou corrompue.

## 9. Interface desktop

L'application doit ressembler a une vraie app :

- fenetre native ;
- icone d'application ;
- titre coherent ;
- pas d'URL visible ;
- pas d'ouverture automatique du navigateur systeme ;
- taille minimale responsive ;
- raccourci pour ouvrir le dossier logs/config en cas de debug.

Pages/ecrans V1 :

- Onboarding cle API ;
- Dashboard principal ;
- Carriere ;
- Modal detail match ;
- Ecran settings.

Settings minimum :

- changer/supprimer la cle API ;
- ouvrir le dossier de donnees ;
- afficher version app ;
- bouton verifier API ;
- bouton recharger assets/cache ;
- toggle lancer au demarrage Valorant (un petit script est lancé au démarrage windows, et détecte si valorant s'ouvre. Au moment où valorant s'ouvre, le script lance l'application).

## 10. Packaging Windows

### Build applicatif

Outil recommande :

- PyInstaller pour produire un executable.

Livrables build :

- `ValorantTracker.exe`;
- assets statiques inclus ;
- templates inclus ;
- dependances Python incluses ;
- runtime config propre ;
- icone `.ico`.

Points importants :

- ne pas embarquer de cle API personnelle ;
- ne pas embarquer `tracker.db` de dev ;
- ne pas embarquer les captures de debug ;
- exclure `.env`, `.idea`, `data/live_api_snapshots`, archives, screenshots.

### Installer

Outil recommande :

- Inno Setup pour produire `ValorantTrackerSetup.exe`.

Installer doit :

- installer l'executable ;
- creer raccourcis ;
- verifier/installer WebView2 Runtime si necessaire ;
- proposer lancement apres installation ;
- permettre desinstallation propre ;
- ne pas supprimer les donnees utilisateur sans confirmation.

## 11. Securite et confidentialite

Donnees sensibles :

- cle API HenrikDev ;
- PUUID Riot ;
- historique local des matchs ;
- logs pouvant contenir noms de joueurs.

Regles :

- ne jamais logguer la cle API ;
- redact tokens Riot dans les logs ;
- stocker la cle via Credential Manager/DPAPI ;
- ne pas envoyer de donnees vers un serveur maison en V1 ;
- afficher clairement que tout reste local ;
- prevoir un bouton `Supprimer mes donnees locales`, avec une double confirmation.

## 12. Logs et debug

L'app doit ecrire des logs dans :

`%APPDATA%\ValorantTracker\logs`

Logs utiles :

- demarrage app ;
- port backend choisi ;
- detection Valorant ;
- erreurs API HenrikDev ;
- erreurs Riot local ;
- migrations DB ;
- sauvegarde match ;
- echec post-match.

Les logs doivent exclure :

- cle API ;
- tokens Riot ;
- entitlements ;
- mots de passe ou secrets.

## 13. Mises a jour

V1 privee :

- distribution manuelle d'un nouvel installer.

V2 possible :

- auto-update via GitHub Releases ou serveur statique ;
- verification de version au demarrage ;
- prompt de mise a jour.

## 14. Tests d'acceptation V1

Installation :

- l'installer installe l'app sur une machine propre ;
- le raccourci lance l'app ;
- l'app ouvre une fenetre native ;
- aucune console visible en usage normal.

Onboarding :

- sans cle API, l'ecran de configuration apparait ;
- une cle invalide affiche une erreur claire ;
- une cle valide est sauvegardee ;
- au prochain lancement, l'onboarding n'apparait plus.

Runtime :

- Valorant ferme : app affiche offline ;
- Valorant ouvert en menu : app detecte le compte ;
- en match : app charge les joueurs ;
- apres match : app sauvegarde le match ;
- carriere : les stats ranked-only restent correctes ;
- filtre act/mode : l'historique change, les stats ranked restent stables selon la regle choisie.

Donnees :

- `tracker.db` est cree dans `%APPDATA%` ;
- une seconde machine/utilisateur a sa propre DB ;
- desinstallation ne supprime pas la DB sans confirmation.

## 15. Roadmap proposee

### Phase 1 - Preparation app locale

- separer chemins dev et chemins production ;
- creer un gestionnaire de config ;
- deplacer DB vers `%APPDATA%`;
- ajouter stockage securise cle API ;
- creer ecran onboarding.

### Phase 2 - Fenetre desktop

- integrer pywebview ;
- lancer FastAPI en background ;
- gerer fermeture propre backend/fenetre ;
- ajouter icone et metadata app.

### Phase 3 - Build executable

- config PyInstaller ;
- inclure templates/static/assets ;
- exclure fichiers dev ;
- produire un `.exe` standalone.

### Phase 4 - Installer

- script Inno Setup ;
- installation WebView2 si besoin ;
- raccourcis ;
- desinstallation propre.

### Phase 5 - Beta amis

- build versionnee ;
- checklist test ;
- collecte manuelle de feedback ;
- correction bugs installation/runtime.

## 16. Questions ouvertes

- Nom final de l'application.
- Icône officielle/personnalisee.
- Distribution : zip prive, Google Drive, GitHub Release privee, Discord ?
- Stockage cle API : Credential Manager obligatoire des la V1 ou DPAPI maison acceptable ?
- Auto-start Windows souhaité ou non ?
- Support Windows uniquement ou prevoir macOS plus tard ?
- Est-ce qu'on veut signer l'executable pour eviter les alertes Windows SmartScreen ?

## 17. Notes techniques evidentes a ne pas oublier

- Le port backend doit etre choisi dynamiquement pour eviter les conflits.
- L'app ne doit pas dependre du cwd pour trouver templates/static.
- En mode PyInstaller, les chemins passent par `sys._MEIPASS`.
- Il faut une commande `reset app data` pour debug.
- Il faut nettoyer le repo avant packaging pour ne pas embarquer les screenshots/snapshots.
- Le `.env` de dev ne doit jamais etre inclus.
- Prevoir un mode `--dev` pour lancer comme aujourd'hui dans le navigateur.
- Prevoir un mode `--portable` plus tard si on veut une version zip sans installer.
