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

## Décisions retenues pour le nouvel installateur

### 0. Point d'entrée unique

Le repo doit converger vers un seul point d'entrée d'installation :
- `install-openclaw-agent.sh`

Le flux update ne doit plus vivre dans un script séparé avec sa propre logique.
Si on garde un jour un alias de confort, il doit rester un wrapper trivial sans logique métier.

### 1. Cible d'installation

Le nouvel installateur ne crée plus d'agent OpenClaw.

Il doit cibler uniquement :
- `main`
- ou un agent déjà configuré dans OpenClaw

Raison : la création d'un agent neuf demande trop de paramétrage implicite ou interactif (routing, allowlist de skills, compte bot, identité, modèle, sessions cibles), ce qui dilue le rôle de l'installeur.

### 2. Modes supportés

Le script doit supporter explicitement :
- `install` : aucun runtime coach exploitable n'est présent
- `update` : installation existante détectée et mise à jour en place
- `repair` : runtime/config existants mais incomplets ou incohérents

Le mode peut être auto-résolu à partir de l'existant, mais le résumé final doit l'indiquer clairement.

### 3. Phases obligatoires

#### Préflight

Avant toute écriture, l'installeur doit résoudre ou vérifier :
- config OpenClaw cible
- agent cible
- workspace cible
- root d'installation
- config métier existante
- manifest existant
- venv existant
- DB existante
- timers systemd existants
- cron weekly existant
- disponibilité de Python
- disponibilité de `systemd --user` si les timers sont demandés
- droits d'écriture sur le workspace et le root d'installation

#### Backup

Avant remplacement, l'installeur doit sauvegarder au minimum :
- fichiers agent remplacés
- config OpenClaw patchée
- config métier remplacée
- manifest remplacé
- unités systemd remplacées si elles sont réécrites

Le backup doit être horodaté et regroupé dans un dossier unique par run.

#### Runtime / package

L'installeur doit ensuite :
- créer ou mettre à jour le venv managé
- installer ou mettre à jour le package Python
- recréer / réparer les symlinks `bin/`
- vérifier que les entrypoints CLI essentiels répondent

#### Fichiers agent

L'installeur doit installer ou mettre à jour :
- prompts / fichiers agent
- playbooks
- skills
- fichiers de contexte agent requis

Il doit préserver explicitement les fichiers que l'on considère comme potentiellement customisés localement (par exemple `SOUL.md`, `IDENTITY.md`, `HEARTBEAT.md`) selon une politique claire et documentée.

#### Données

L'installeur doit :
- créer ou migrer la DB SQLite
- vérifier les chemins de données
- créer les dossiers nécessaires (`tokens/`, data dir, etc.)

#### Automations

L'installeur doit pouvoir créer ou mettre à jour :
- le timer `systemd --user` de sync Garmin
- le timer `systemd --user` d'export Garmin des séances du lendemain
- le cron OpenClaw de weekly planning

### 4. Weekly planning : paramètres cibles

Pour créer ou mettre à jour le weekly planning, il faut au minimum :
- un modèle
- une cible d'exécution / de livraison (`sessionKey` ou delivery explicite)
- une timezone
- un schedule

L'installeur doit auto-résoudre au maximum :
- `agent_id`
- workspace
- modèle par défaut de l'agent
- timezone déjà connue
- session cible déjà connue
- nom du job cron

Il ne doit demander que le strict minimum manquant.

### 5. Idempotence

Le script doit être idempotent :
- un rerun sur la même cible ne doit pas dupliquer les timers, cron jobs, symlinks ou fichiers
- un update doit remplacer / migrer, pas empiler
- un état déjà correct doit produire un no-op ou une réinstallation minimale

## Config métier persistée

La config métier persistée contient uniquement le durable, métier, non auto-discoverable.

Elle ne doit pas contenir les détails techniques de version, de chemins, de runtime ou de provisioning.

### Champs attendus

Exemples de contenu légitime :
- configuration du weekly planning
- timezone métier du coach
- cible du weekly planning (`sessionKey` ou delivery)
- modèle du weekly planning si différent du défaut résolu
- politiques d'automatisation Garmin si elles sont produit et non simplement techniques

### Exemple de structure

```json
{
  "schema_version": 1,
  "agent_id": "garmin-coach",
  "weekly_planning": {
    "enabled": true,
    "model": "azure/gpt-5.4-1",
    "timezone": "UTC",
    "schedule": "0 18 * * 0",
    "session_key": "agent:garmin-coach:telegram:direct:8771763758"
  },
  "garmin": {
    "sync_enabled": true,
    "export_tomorrow_enabled": true
  }
}
```

### Contrat JSON v1

#### `coach-config.json`

- `schema_version` : entier, requis, vaut `1`
- `agent_id` : string, requis
- `weekly_planning` : objet, requis
  - `enabled` : bool, requis
  - `name` : string, optionnel mais recommandé
  - `model` : string, optionnel
  - `timezone` : string IANA, optionnel
  - `schedule` : string, optionnel
  - `session_key` : string, optionnel
  - `delivery` : objet, optionnel
    - `to` : string, optionnel
    - `channel` : string, optionnel
    - `account_id` : string, optionnel
- `garmin` : objet, requis
  - `sync_enabled` : bool, requis
  - `export_tomorrow_enabled` : bool, requis

Contraintes v1 :
- `weekly_planning.session_key` et `weekly_planning.delivery.*` sont mutuellement alternatifs : au moins un mécanisme de routage doit exister pour activer réellement le weekly planning.
- `weekly_planning.enabled=true` n'implique pas que le cron a été provisionné avec succès ; l'état technique réel reste dans le manifest.

### Exclusions explicites

La config métier ne doit pas contenir :
- chemins locaux
- version installée
- commit / tag Git
- état du venv
- timestamps techniques d'installation
- état de provisioning systemd / cron technique

## Manifest technique d'installation

Le manifest contient uniquement l'état technique et versionné de l'installation.

### Champs attendus

Le manifest doit stocker au moins :
- `schema_version`
- `app_version`
- `git.tag`
- `git.commit`
- `git.source` (`tag`, `branch`, `commit`, `local`)
- `git.dirty`
- chemins runtime / workspace / install root / data dir / venv
- `agent_id`
- chemin de config OpenClaw utilisé
- features provisionnées
- timestamp d'installation / update
- chemin du backup créé par ce run

### Exemple de structure

```json
{
  "schema_version": 1,
  "app_version": "0.2.8",
  "git": {
    "tag": "v0.2.8",
    "commit": "69b3cb1df081c7fd19edaa5cdd7456b2523ba14b",
    "source": "tag",
    "dirty": false
  },
  "paths": {
    "workspace_dir": "/home/coach",
    "install_root": "/home/coach/.garmin-coach-agent",
    "data_dir": "/home/coach/.garmin-coach-agent/data",
    "managed_venv": "/home/coach/.garmin-coach-agent/.venv/bin/python"
  },
  "target": {
    "agent_id": "garmin-coach",
    "openclaw_config_path": "/home/mwn/.openclaw/openclaw.json"
  },
  "features": {
    "python_runtime": true,
    "agent_files": true,
    "db_migrated": true,
    "systemd_sync": true,
    "systemd_export": true,
    "weekly_planning_cron": true
  },
  "backup": {
    "last_backup_dir": "/home/coach/.garmin-coach-agent/backups/2026-06-11T16-00-00Z"
  },
  "installed_at": "2026-06-11T16:00:00Z"
}
```

### Contrat JSON v1

#### `manifest.json`

- `schema_version` : entier, requis, vaut `1`
- `install_mode` : string requise, parmi `install|update|repair`
- `app_version` : string, requise
- `git` : objet, requis
  - `tag` : string, optionnel
  - `commit` : string, optionnel
  - `source` : string requise, parmi `tag|branch|commit|local`
  - `dirty` : bool, requis
- `paths` : objet, requis
  - `workspace_dir` : string, requis
  - `install_root` : string, requis
  - `data_dir` : string, requis
  - `managed_venv` : string, requis
- `target` : objet, requis
  - `agent_id` : string, requis
  - `openclaw_config_path` : string, requis
- `features` : objet, requis
  - `python_runtime` : bool, requis
  - `agent_files` : bool, requis
  - `db_migrated` : bool, requis
  - `systemd_sync` : bool, requis
  - `systemd_export` : bool, requis
  - `weekly_planning_cron` : bool, requis
- `backup` : objet, requis
  - `last_backup_dir` : string, requis
- `installed_at` : timestamp UTC ISO-8601, requis

## Politique actuelle de compatibilité de schéma

Pour cette passe :

- le schéma JSON v1 est documenté et devient le contrat cible
- aucune couche générale de migration versionnée n'est requise tant que le schéma ne bouge pas
- seule la transition legacy `manifest.txt` -> `manifest.json` doit rester tolérée
- si un futur changement casse la structure d'un fichier JSON, il devra :
  - incrémenter `schema_version`
  - mettre à jour la doc avec le nouveau contrat
  - décider explicitement à ce moment-là s'il faut une migration ou une rupture assumée

## Source d'installation

Le manifest doit permettre de distinguer clairement :
- install depuis une release taggée
- install depuis une branche
- install depuis un commit précis
- install depuis un checkout local

Cette info est importante pour :
- savoir si l'installation est une release propre ou un proto local
- savoir si un update automatique est raisonnable
- expliquer les garanties de reproductibilité

## Résumé final attendu

À la fin du run, le script doit afficher un résumé lisible contenant au moins :
- mode (`install`, `update`, `repair`)
- agent ciblé
- version installée
- source installée
- DB créée / migrée / inchangée
- timers systemd créés / mis à jour / ignorés
- cron weekly créé / mis à jour / ignoré
- chemins des fichiers de config / manifest écrits
- chemin du backup produit

## Hors scope de ce refactor

Pour cette passe, on ne cherche pas à faire :
- création d'un nouvel agent OpenClaw
- UX interactive avancée
- rollback complet automatique
- uninstall complet
- auto-discovery magique de paramètres non fiables

## Ticket lié

- Issue GitHub #16: `Installer/update overhaul: persisted coach config + versioning contract`

## Prochaines étapes probables

1. figer le schéma exact de la config métier persistée
2. figer le schéma exact du manifest technique
3. implémenter / consolider le flux install/update/repair dans ce point d'entrée unique
4. brancher ensuite le téléchargement / l'usage des artefacts de release dans l'installeur
