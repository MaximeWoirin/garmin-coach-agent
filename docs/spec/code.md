# Architecture du code

## But

Cette page décrit comment structurer le code Python du projet.

L’idée est :
- un vrai projet Python
- un package partagé pour la logique métier
- des scripts très fins comme points d’entrée
- pas de logique dispersée dans des fichiers shell ou des scripts isolés

Le flux d'installation OpenClaw doit suivre cette règle aussi :
- `scripts/install-openclaw-agent.sh` reste un bootstrap fin
- la logique d'installation/update/repair vit dans `garmin_coach.install_openclaw_agent`

## Principe

On sépare clairement :

- **CLI / scripts** : interface d’entrée
- **logique métier** : règles et opérations réutilisables
- **accès DB** : lecture / écriture SQLite
- **intégration Garmin** : auth, sync, export
- **modèles communs** : enums, validation, sérialisation JSON

## Structure actuelle (vue simplifiée)

```text
.
├── pyproject.toml
├── README.md
├── migrations/
│   ├── 0001_init.sql
│   ├── 0002_add_sync_runs.sql
│   └── 0003_plan_session_status.sql
├── docs/
│   └── spec/
│       ├── README.md
│       ├── architecture.md
│       ├── code.md
│       ├── database.md
│       ├── tools.md
│       ├── scripts.md
│       ├── export-workflow.md
│       └── agent.md
├── agent/
│   ├── AGENTS.md
│   ├── BOOTSTRAP.md
│   ├── HEARTBEAT.md
│   ├── IDENTITY.md
│   ├── README.md
│   ├── SOUL.md
│   ├── SYSTEM.md
│   ├── TOOLS.md
│   ├── skills/
│   │   └── <skill>/SKILL.md
│   └── playbooks/
│       ├── daily_coaching.md
│       ├── weekly_planning.md
│       ├── sync_and_review.md
│       └── fallback_no_garmin.md
├── [project.scripts]
│   ├── auth-garmin
│   ├── sync-garmin
│   ├── export-plan-garmin
│   ├── get-activities
│   ├── get-fitness-state
│   ├── get-goals
│   ├── get-constraints
│   ├── get-current-plan
│   ├── create-goal
│   ├── create-plan-draft
│   ├── create-plan-session
│   ├── delete-plan-session
│   ├── set-plan-status
│   ├── set-plan-session-status
│   ├── create-constraint
│   ├── delete-constraint
│   └── set-constraint-status
└── garmin_coach/
    ├── __init__.py
    ├── config.py
    ├── db.py
    ├── enums.py
    ├── jsonio.py
    ├── create_goal.py
    ├── garmin/
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── client.py
    │   ├── sync.py
    │   └── export.py
    ├── activities/
    │   ├── __init__.py
    │   └── read.py
    ├── metrics/
    │   ├── __init__.py
    │   └── read.py
    ├── constraints/
    │   ├── __init__.py
    │   ├── read.py
    │   ├── write.py
    │   └── status.py
    └── plans/
        ├── __init__.py
        ├── read.py
        ├── write.py
        └── status.py
```

## Ce qui va où

### `pyproject.toml`
Le point d’entrée du projet Python.

Il doit contenir :
- nom du package
- dépendances
- version Python
- éventuels scripts installables plus tard

### `agent/`
Contient la documentation d’orchestration LLM et les skills métier du coach.

Responsabilités :
- rôle et règles du coach
- ton et posture conversationnelle
- mapping entre intentions et scripts
- skills métier alignés avec les scripts publics
- playbooks d’usage
- fichiers de contexte versionnés

Ce dossier ne doit pas devenir un fourre-tout.
La mémoire runtime volatile doit vivre hors Git.

### Console Scripts (`[project.scripts]`)
Contient les scripts d’entrée appelés par l’agent ou par cron.

Règle :
- ces fichiers doivent être **très fins**
- ils parsèment les arguments
- appellent une fonction Python
- renvoient le JSON final

Ils ne doivent pas contenir la vraie logique métier.

Même principe pour l'installeur OpenClaw :
- le shell bootstrappe l'environnement
- le module Python porte l'orchestration réelle

### `garmin_coach/config.py`
Gestion de la configuration locale.

Exemples :
- chemin de la DB SQLite
- chemin du store de tokens Garmin
- options d’environnement

### `garmin_coach/db.py`
Couche d’accès SQLite.

Responsabilités :
- ouvrir la base
- helpers de connexion
- transactions simples
- utilitaires communs SQL
- exécution des migrations

On évite de mettre ici des règles métier.

Le module doit porter un runner minimal de migrations :
- création de `schema_migrations` si besoin
- lecture du dossier `migrations/`
- application dans l’ordre
- enregistrement des versions appliquées

### `garmin_coach/enums.py`
Enums canoniques du projet.

Exemples :
- statuts de plans
- statuts de sessions
- statuts de contraintes
- types de contraintes

Le but est d’avoir une seule source de vérité pour les valeurs canonique.

### `garmin_coach/jsonio.py`
Sortie JSON commune.

Responsabilités :
- structure de réponse standard
- sérialisation propre
- erreurs homogènes

Ça évite que chaque script sorte un JSON légèrement différent.

## Sous-packages métier

### `garmin_coach/garmin/`
Tout ce qui parle à Garmin.

#### `auth.py`
- login initial
- re-login si refresh token invalide
- gestion MFA
- lecture / écriture des tokens

#### `client.py`
- création du client `python-garminconnect`
- chargement du store de tokens
- configuration commune

#### `sync.py`
- import des activités
- import des métriques
- logique de réconciliation appelée par `sync-garmin`

#### `export.py`
- export des séances de plan vers Garmin
- mapping vers les payloads attendus
- récupération des ids Garmin

### `garmin_coach/activities/`
Lecture des activités réelles importées.

#### `read.py`
- lecture des activités sur une plage
- filtres
- résumé simple

### `garmin_coach/metrics/`
Lecture des métriques physiologiques.

#### `read.py`
- lecture des daily metrics
- résumés de tendance
- snapshot fitness state

### `garmin_coach/constraints/`
Gestion des contraintes.

#### `read.py`
- lecture des contraintes
- filtres par scope / status

#### `write.py`
- création d’une contrainte
- suppression d’une contrainte

#### `status.py`
- changement de statut `active | inactive`

### `garmin_coach/plans/`
Gestion des plans et des sessions.

#### `read.py`
- lecture du plan courant
- lecture des séances associées

#### `write.py`
- création de plan draft
- création de session
- suppression de session

#### `status.py`
- changement de statut du plan
- changement de statut d’une session
- éventuelle cascade plan → sessions

## Règles de structuration

### 1. Les scripts sont fins
Un script doit surtout :
- lire les args
- appeler le bon service
- écrire du JSON

### 2. La logique partagée vit dans le package
Tout ce qui peut servir à plusieurs scripts doit aller dans `garmin_coach/`.

### 3. Une responsabilité par module
On évite les gros fichiers fourre-tout.

### 4. Les migrations vivent hors du code métier
Les fichiers SQL vont dans `migrations/`.
Le runner vit dans `garmin_coach/db.py`.

### 5. La DB n’est pas exposée directement à l’agent
L’agent appelle des scripts, pas du SQL.

### 6. Garmin est isolé
Tout le code Garmin reste groupé dans `garmin_coach/garmin/`.

## Flux type

### Auth
- `auth-garmin`
- appelle `garmin_coach.garmin.auth`
- écrit les tokens

### Sync
- `sync-garmin`
- appelle `garmin_coach.garmin.sync`
- écrit activités + métriques + réconciliation

### Lecture contraintes
- `get-constraints`
- appelle `garmin_coach.constraints.read`

### Création session
- `create-plan-session`
- appelle `garmin_coach.plans.write`

### Export Garmin
- `export-plan-garmin`
- appelle `garmin_coach.garmin.export`

## Ce qu’on évite

- scripts shell avec logique métier
- duplication de validation entre plusieurs scripts
- SQL recopié partout
- code Garmin mélangé avec le code plan/contraintes
- un seul énorme fichier Python pour tout le projet

## Verdict

Pour la V0, il faut un **vrai petit projet Python**, pas une collection de scripts isolés.

- `[project.scripts]` = interfaces CLI
- `garmin_coach/` = logique partagée
- `docs/spec/` = contrat et architecture
