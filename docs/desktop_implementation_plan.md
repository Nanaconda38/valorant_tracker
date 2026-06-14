# Valorant Tracker Desktop V1 - Implementation Plan

Ce plan suit `specifications.md` et part de l'etat actuel du projet : le coeur FastAPI, le polling Riot local, l'API HenrikDev, la base SQLite et l'interface web existent deja. L'objectif V1 est donc de transformer l'application locale actuelle en application Windows distribuable.

## 1. Preparation des chemins production

- Creer un module central `app_paths.py`.
- Deplacer les donnees runtime vers `%APPDATA%\ValorantTracker`.
- Utiliser `%APPDATA%\ValorantTracker\tracker.db` comme base SQLite par defaut.
- Prevoir les dossiers :
  - `logs/`
  - `cache/`
  - `settings.json`
- Rendre les chemins `templates`, `static` et assets compatibles avec le mode developpement et le mode PyInstaller (`sys._MEIPASS`).
- Supprimer les dependances implicites au dossier courant pour le runtime applicatif.

## 2. Configuration locale

- Ajouter un gestionnaire de configuration locale.
- Stocker les preferences non sensibles dans `%APPDATA%\ValorantTracker\settings.json`.
- Gerer au minimum :
  - premiere ouverture ;
  - version app ;
  - debug ;
  - cache ;
  - lancement au demarrage ;
  - choix eventuels d'interface.
- Garder `.env` seulement pour le developpement local.

## 3. Stockage securise de la cle HenrikDev

- Ajouter un service `secrets.py`.
- Cible V1 : Windows Credential Manager ou DPAPI.
- Fallback temporaire acceptable : fichier config local utilisateur, explicitement marque comme temporaire.
- Ne jamais embarquer de cle API dans le build.
- Remplacer la lecture directe `HENRIK_API_KEY` depuis l'environnement par une lecture via ce service.

## 4. Onboarding et settings

- Ajouter un ecran `Configuration HenrikDev API`.
- Ajouter les actions :
  - ouvrir HenrikDev ;
  - verifier une cle ;
  - sauvegarder une cle valide ;
  - continuer sans cle avec avertissement ;
  - changer ou supprimer la cle depuis les settings.
- Ajouter les endpoints FastAPI :
  - `GET /api/config/status`
  - `POST /api/config/henrik-key/verify`
  - `POST /api/config/henrik-key`
  - `DELETE /api/config/henrik-key`
  - `GET /api/settings`
- Ajouter dans les settings :
  - ouvrir le dossier donnees ;
  - ouvrir le dossier logs ;
  - afficher la version ;
  - verifier l'API ;
  - recharger assets/cache ;
  - activer/desactiver le lancement au demarrage.

## 5. Logs et hygiene des secrets

- Ecrire les logs dans `%APPDATA%\ValorantTracker\logs`.
- Remplacer les sorties debug sensibles par un logger filtre.
- Redacter :
  - cle HenrikDev ;
  - tokens Riot ;
  - entitlements ;
  - headers d'autorisation ;
  - mots de passe.
- Ajouter des messages propres pour :
  - Valorant ferme ;
  - lockfile introuvable ;
  - HenrikDev absent ou invalide ;
  - rate-limit HenrikDev ;
  - Riot local indisponible ;
  - DB verrouillee ou corrompue.

## 6. Fenetre desktop pywebview

- Ajouter `desktop_main.py`.
- Lancer FastAPI en arriere-plan sur `127.0.0.1`.
- Choisir un port libre dynamiquement.
- Ouvrir une fenetre native pywebview basee sur WebView2.
- Masquer toute URL et eviter l'ouverture du navigateur systeme.
- Gerer la fermeture propre de la fenetre et du backend.
- Garder un mode developpement utilisable sans packaging.

## 7. Build executable PyInstaller

- Ajouter la configuration PyInstaller.
- Inclure :
  - `templates/`
  - `static/`
  - assets Valorant ;
  - modules Python necessaires.
- Exclure :
  - `.env`
  - `tracker.db`
  - logs ;
  - screenshots ;
  - snapshots debug ;
  - `.idea`
  - dossiers temporaires.
- Produire `ValorantTracker.exe`.

## 8. Installer Windows

- Ajouter un script Inno Setup.
- Installer l'application dans `%LOCALAPPDATA%\ValorantTracker` ou `Program Files` selon le mode choisi.
- Creer :
  - raccourci Bureau ;
  - raccourci Menu Demarrer.
- Verifier ou installer WebView2 Runtime.
- Proposer le lancement apres installation.
- Ne pas supprimer les donnees utilisateur sans confirmation.

## 9. Lancement automatique lie a Valorant

- Ajouter un toggle dans les settings.
- Creer/supprimer une entree de demarrage Windows.
- Lancer un petit watcher au demarrage Windows.
- Quand Valorant est detecte, ouvrir l'application.

## 10. Validation V1

- Installer sur une machine propre.
- Lancer via raccourci sans console visible.
- Afficher l'onboarding sans cle.
- Afficher une erreur claire avec une cle invalide.
- Sauvegarder une cle valide.
- Ne plus afficher l'onboarding au lancement suivant.
- Afficher `offline` quand Valorant est ferme.
- Detecter le compte quand Valorant est ouvert.
- Charger les joueurs en match.
- Sauvegarder le post-match dans `%APPDATA%\ValorantTracker\tracker.db`.
- Conserver les donnees apres desinstallation sauf confirmation explicite.

## Ordre d'implementation recommande

1. Chemins runtime et ressources.
2. Configuration locale.
3. Secrets HenrikDev.
4. Onboarding et settings.
5. Logs securises.
6. Launcher desktop.
7. PyInstaller.
8. Inno Setup.
9. Autostart Valorant.
10. Beta test amis.
