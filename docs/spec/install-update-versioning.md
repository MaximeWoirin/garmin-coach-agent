# Install / Update / Versioning Notes

But: document de référence de travail pour cadrer l'overhaul installation/update/versioning du `garmin-coach-agent`.

## Contexte

Le besoin vient de plusieurs constats observés en prototypage :

- l'install/update actuel mélange logique produit, logique runtime et contexte utilisateur
- certaines infos nécessaires au coach ne sont pas auto-discoverables de façon fiable depuis la seule config OpenClaw de l'agent
- le flux fresh install / reinstall / update doit devenir plus robuste
- le versioning actuel ne doit plus reposer sur des bumps manuels dans `pyproject.toml`

## Direction générale retenue

### 1. Config métier persistée

Il faut définir une config métier persistée du coach, distincte du manifest technique d'installation.

Cette config doit contenir ce qu'on ne peut pas auto-discover de façon fiable, par exemple :

- cible du weekly planning (`sessionKey` ou delivery explicite)
- timezone / horaire de weekly planning
- politiques d'automatisation Garmin si elles ne sont pas implicites
- autres préférences durables réellement nécessaires au comportement du coach

Objectif :
- demander le minimum à l'installation
- réutiliser cette config sur update / reinstall
- pouvoir distinguer ce qui est auto-discoverable de ce qui doit être fourni explicitement

### 2. Séparation config métier vs manifest d'installation

#### Config schema

Version du format de la config métier persistée :
- structure des champs
- sémantique des réglages coach
- migrations de config métier

#### Manifest schema

Version du format du manifest d'installation :
- version app installée
- commit / tag / source installée
- chemins runtime / install root / workspace
- features provisionnées
- état technique de l'installation

Règle mentale :
- config schema = comment le coach doit se comporter
- manifest schema = comment cette installation est câblée

### 3. Auto-discovery

L'approche cible n'est ni 100% manuelle, ni 100% magique.

On veut :

1. auto-discover ce qui est évident
   - agent id
   - workspace
   - install root
   - modèle par défaut
   - certains defaults d'horaires / timezone
   - éléments runtime déjà installés

2. réutiliser ce qui existe déjà
   - config métier persistée
   - cron existant
   - routing/delivery déjà connue si retrouvable de façon fiable

3. demander seulement le minimum manquant
   - typiquement la vraie cible du weekly planning si elle n'est pas connue

## Versioning Git - direction retenue à challenger

### Objectif

Avoir une stratégie :
- compatible `main` protégé
- PR-only
- install/update-friendly
- où la version applicative a pour source de vérité les tags GitHub

### Propositions

#### Branches

Convention de travail :
- `feat/*`
- `fix/*`
- `refactor/*`
- `docs/*`
- `chore/*`
- `spike/*`

Le nom de branche doit rester un **signal**, pas la seule source de vérité du bump.

#### PR

`main` protégé :
- push direct interdit
- merge via PR uniquement
- CI obligatoire
- review obligatoire
- idéalement squash merge only

Il faut une intention de release explicite sur la PR, par exemple via label :
- `release:major`
- `release:minor`
- `release:patch`
- `release:none`

Le nom de branche peut suggérer un label par défaut, mais le label PR doit rester la décision finale.

#### Tags

Source de vérité de la version app :
- tags GitHub `vMAJOR.MINOR.PATCH`

Bump proposé :
- patch -> `x.y.(z+1)`
- minor -> `x.(y+1).0`
- major -> `(x+1).0.0`
- major doit rester explicite

#### Build / packaging

Direction préférée :
- ne plus bumper `pyproject.toml` manuellement
- dériver la version package depuis le tag Git au moment du build/release
- garder `pyproject.toml` comme support packaging Python, pas comme source de vérité produit

#### Runtime / install

L'installation devra pouvoir stocker au moins :
- version app résolue
- commit Git
- tag Git
- source d'installation (`tag`, `branch`, `commit`, `local`)
- état `dirty` éventuel

Objectif :
- différencier un install release propre d'un install de prototypage
- clarifier les garanties d'update selon le mode d'installation

## Ticket lié

- Issue GitHub #16: `Installer/update overhaul: persisted coach config + versioning contract`

## Prochaines étapes probables

1. cadrer précisément quels paramètres coach ne sont pas auto-discoverables
2. concevoir les 2 fichiers cibles : config métier persistée + manifest technique
3. définir les règles PR / labels / tags / release
4. seulement ensuite revoir le script d'installation et d'update
