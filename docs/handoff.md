# Handoff - Valorant Local Tracker

Ce fichier sert a reprendre le projet dans une nouvelle discussion Codex sans perdre le contexte.

## Projet

- Dossier: `C:\Users\naelc\PycharmProjects\valorant_tracker`
- Stack: FastAPI, Jinja2, Vanilla JS/CSS, SQLite local.
- App locale: `http://127.0.0.1:8000`
- Commande serveur:
  ```powershell
  .\venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
  ```
- Preference utilisateur: quand Codex teste la page, utiliser un Chrome visible/headed.

## Etat Actuel

Le tracker local fonctionne avec:

- Detection Riot/LCU/GLZ pour l'etat de session.
- Vue dashboard live/pregame/core-game existante.
- Historique carriere local en SQLite.
- Import des dernieres parties competitives.
- Support multi-utilisateur sur la meme machine via PUUID.
- Assets locaux Valorant:
  - agents
  - ranks
  - maps
  - bannieres de maps
- Details de match avec onglets inspires de Tracker.gg:
  - Scoreboard
  - Performance
  - Economy
  - Rounds
  - Duels
- Live tracker abandonne volontairement: l'objectif est d'eviter Overwolf et de ne pas utiliser d'overlay espion.

## Changements Recents Importants

### Extraction et calibration Tracker Score

Objectif utilisateur: rapprocher notre Tracker Score du TRS Tracker.gg.

Travail fait:

- Anciennes donnees archivees dans:
  `data/archives/scoreboard_screens_baseline_20260614_040622.zip`
- Nouveau batch de screenshots zoomes traite depuis:
  `data/scoreboard_screens`
- L'extracteur a ete adapte aux screenshots zoomes:
  `tools/extract_tracker_scoreboards.py`
- Correction majeure:
  - avant: seulement 29 matchs extraits
  - apres patch: 53 matchs valides extraits
  - 530 lignes ajoutees
- Les refus restants etaient justifies:
  - 3 ecrans Tracker.gg en chargement
  - 1 doublon
  - 2 scorelines non finales/invalides (`0-5`, `13-13`)

Tables SQLite de calibration:

- Table principale:
  `tracker_score_samples`
- Table separee du nouveau batch:
  `tracker_score_samples_stage_zoomed_20260614`
- Comptes:
  - `baseline_20260614`: 309 samples
  - `zoomed_20260614`: 530 samples
  - total: 839 samples

Commandes utiles:

```powershell
.\venv\Scripts\python.exe .\tools\extract_tracker_scoreboards.py
.\venv\Scripts\python.exe .\tools\calibration_store.py summary
.\venv\Scripts\python.exe .\tools\calibration_store.py summary --table tracker_score_samples_stage_zoomed_20260614
.\venv\Scripts\python.exe .\tools\calibrate_tracker_score.py
```

### Nouveau modele Tracker Score

Le calcul simple lineaire a ete remplace par un modele non lineaire Gradient Boosting.

Fichiers:

- Source de calibration:
  `tools/calibrate_tracker_score.py`
- Predicteur genere utilise par l'app:
  `data/predict_trs_generated.py`
- App backend:
  `app.py`

Resultat sur les 839 samples:

- MAE: `0.8`
- p95: `2`
- erreur max: `4`

Important:

- La contrainte `+-5` est atteinte sur les samples fournis.
- En validation croisee, l'erreur max reste beaucoup plus haute.
- Ne pas vendre ce modele comme garantie `+-5` sur des matchs jamais vus.
- C'est un modele tres proche des exemples Tracker.gg captures, mais il peut overfit.

### Badges Tracker Score

L'utilisateur a demande des icones type Tracker.gg, mais originales et plus style Valorant/tactical FPS.

Assets crees:

- Planche complete:
  `static/assets/tracker-score-badges-valorant-v2.png`
- Badges decoupes:
  - `static/assets/tracker-score/trs-0-199.png`
  - `static/assets/tracker-score/trs-200-399.png`
  - `static/assets/tracker-score/trs-400-599.png`
  - `static/assets/tracker-score/trs-600-799.png`
  - `static/assets/tracker-score/trs-800-999.png`
  - `static/assets/tracker-score/trs-1000.png`

Integration faite dans:

- `static/js/app.js`
- `static/css/style.css`
- `app.py`

Affichage actuel:

- resume carriere: badge + score
- historique carriere: badge + TRS pour les matchs competitifs
- cartes joueurs live/post-match: badge + score
- modale detail de match: colonne `TRS` avec badge + score

Correction importante:

- Dans la DB carriere, le champ `score` des matchs est le score Riot/combat brut, pas notre Tracker Score.
- `app.py` calcule maintenant un champ `tracker_score` pour chaque match competitif dans `/api/career`.
- Le frontend utilise `match.tracker_score`, pas `match.score`, pour eviter des scores absurdes type `5963`.

Tests visuels faits dans Chrome visible:

- Dashboard: badges visibles, aucun asset casse.
- Modale Scoreboard: 10 badges TRS visibles, aucun asset casse.

## Fichiers Modifies / Non Commites

Etat git observe:

```text
 M .gitignore
 M app.py
 M data/predict_trs_generated.py
 M tools/extract_tracker_scoreboards.py
 M static/css/style.css
 M static/js/app.js
?? .idea/
?? tools/calibration_store.py
?? static/assets/tracker-score-badges-valorant-v2.png
?? static/assets/tracker-score/
```

Notes:

- `.idea/` est apparu non tracke. Ne pas le commit sans demander.
- `tools/calibration_store.py` est un nouvel outil local utile, probablement a garder.
- `data/tracker_score_samples.csv`, `tracker.db`, screenshots et archives sont ignores.
- `.gitignore` contient des changements lies aux donnees locales et assets temporaires.

## Commandes de Verification

Backend:

```powershell
.\venv\Scripts\python.exe -m py_compile .\app.py .\tools\calibrate_tracker_score.py .\tools\extract_tracker_scoreboards.py .\tools\calibration_store.py .\data\predict_trs_generated.py
```

Extraction:

```powershell
.\venv\Scripts\python.exe .\tools\extract_tracker_scoreboards.py
```

Calibration:

```powershell
.\venv\Scripts\python.exe .\tools\calibrate_tracker_score.py
```

Career API sanity check:

```powershell
@'
import json, urllib.request
payload=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/career', timeout=5))
print('summary', payload.get('tracker_score'))
for match in payload.get('recent_matches', [])[:5]:
    print(match.get('gamemode'), match.get('acs'), match.get('score'), match.get('tracker_score'))
'@ | .\venv\Scripts\python.exe -
```

Resultat attendu:

- `summary` autour de la valeur TRS carriere.
- Matchs `competitive`: `tracker_score` present et entre 100 et 1000.
- Modes non competitifs: `tracker_score` absent ou `None`.

## Points d'Attention

- Ne pas essayer de contourner Cloudflare sur Tracker.gg.
- Ne pas relancer l'idee Overwolf/live overlay.
- Pour les tests UI, utiliser Chrome visible/headed.
- Le champ DB `score` est ambigu:
  - dans certains payloads Riot, c'est du combat score total
  - pour le TRS, utiliser explicitement `tracker_score`
- Le modele `data/predict_trs_generated.py` est volumineux car il contient les arbres du Gradient Boosting.
- `node` n'est pas disponible dans le shell PowerShell actuel, donc `node --check static/js/app.js` ne marche pas.

## Prochaines Bonnes Etapes

1. Nettoyer le git status:
   - decider si `.idea/` doit rester ignoree
   - verifier `.gitignore`
   - garder `tools/calibration_store.py`
   - garder les assets `static/assets/tracker-score/`
2. Faire un commit logique:
   - extraction/calibration TRS
   - integration badges TRS
   - correction `tracker_score` dans `/api/career`
3. Ajouter un petit fallback UI si `tracker_score` manque dans une game competitive.
4. Eventuellement affiner les badges:
   - generer des assets plus propres en vrai transparent
   - ou remplacer les crops PNG par des SVG maison plus nets.
5. Ajouter tests backend simples pour:
   - `calculate_tracker_score`
   - `/api/career` expose `tracker_score` pour ranked
   - pas d'utilisation de `score` brut comme TRS.

## Resume Court a Donner au Nouvel Assistant

On travaille sur un tracker Valorant local FastAPI/JS. On vient d'ajouter un modele TRS non lineaire calibre sur 839 samples Tracker.gg, avec MAE 0.8 et max error 4 sur les samples. On a aussi cree et integre 6 badges Tracker Score originaux style Valorant. Le frontend affiche maintenant badge + TRS dans la carriere, les cartes joueurs et la modale scoreboard. Attention: `match.score` en DB est le score Riot brut, pas le Tracker Score; utiliser `match.tracker_score`. Tests visuels Chrome visibles OK sur `127.0.0.1:8000`.
