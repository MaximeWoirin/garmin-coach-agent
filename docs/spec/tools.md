# Outils — structure fonctionnelle

## But

Cette page sert d’index stable pour l’architecture des outils.

Le principe est simple :
- on découpe le système par **bloc métier**
- on décrit chaque bloc avec le même cadre
- on ajoute les scripts petit à petit sans casser la vue d’ensemble
- l’agent consomme des outils génériques, pas des scripts “coach” spécialisés

## Navigation

- [`objectives.md`](tools/objectives.md)
- [`activities.md`](tools/activities.md)
- [`metrics.md`](tools/metrics.md)
- [`constraints.md`](tools/constraints.md)
- [`plans.md`](tools/plans.md)

## Blocs métier

| Bloc | Rôle | État |
|---|---|---|
| Objectifs | Cap moyen terme, événement cible, niveau d’ambition | lecture + création OK |
| Activités | Séances réelles, import Garmin, lecture, réconciliation | lecture + sync OK, réconciliation à affiner |
| Métriques physiologiques | Daily metrics, readiness, lecture, synchro | presque complet |
| Contraintes | Contraintes de vie / training / santé / dispo | lecture + écriture de base OK |
| Plans | Plan hebdo, séances planifiées, export Garmin, revue | socle V1 implémenté |

## Ce qu’on veut garder stable

- des scripts **génériques**
- une sortie **JSON** lisible
- pas de SQL libre exposé à l’agent
- pas de logique cachée dans le prompt
- des noms de scripts stables et documentés

## Cadre de description d’un bloc

Pour chaque bloc métier, on garde la même fiche :

- **Rôle** : ce que le bloc couvre
- **Existant** : ce qui est déjà cadré
- **Manquant** : ce qu’il faut encore ajouter
- **Scripts** : les points d’entrée attendus
- **Dépendances** : ce que ce bloc lit ou écrit
- **Questions ouvertes** : les choix qui restent à trancher

## Cartographie rapide

### Objectifs

- **Existant** : `get-goals`, `create-goal`, table `training_goals`
- **Manquant** : lifecycle objectif (`set-goal-status` éventuel)
- **Dépendances** : SQLite, blocs d’entraînement, contraintes liées

### Activités

- **Existant** : `sync-garmin`, `get-activities`, `get-pending-debriefs`, `save-activity-debrief`, réconciliation de base au fil de la sync
- **Manquant** : matching plan ↔ activité plus fin, gestion des corrections tardives, orchestration proactive OpenClaw au-dessus des débriefs
- **Dépendances** : Garmin source, SQLite, `plan_activity_matches`, `activity_debriefs`

### Métriques physiologiques

- **Existant** : `sync-garmin`, `get-fitness-state`
- **Manquant** : rien de bloquant en V0
- **Dépendances** : Garmin source, SQLite, `daily_metrics`

### Contraintes

- **Existant** : `get-constraints`, `create-constraint`, `delete-constraint`, `set-constraint-status`
- **Manquant** : lifecycle plus riche éventuel, normalisation plus poussée si le besoin apparaît
- **Dépendances** : mémoire agent pour le durable, SQLite pour l’état actif/historique

### Plans

- **Existant** : schéma DB (`training_blocks`, `training_plans`, `plan_sessions`, `plan_reviews`), `get-current-plan`, `create-plan-draft`, `create-plan-session`, `delete-plan-session`, `set-plan-status`, `set-plan-session-status`, `export-plan-garmin`
- **Manquant** : mise à jour granulaire de séance sans delete + recreate, revue plus structurée, réconciliation plus riche
- **Dépendances** : objectifs, contraintes, activités, métriques physiologiques, historique du plan

## Authentification Garmin

- `auth-garmin` fait partie du socle déjà implémenté
- il sert au premier setup et aux ré-authentifications si le refresh token expire ou est révoqué
- les scripts métier (`sync-garmin`, `export-plan-garmin`) consomment ensuite les tokens existants

## Progression attendue

On peut remplir ce dossier progressivement :

1. figer le vocabulaire du bloc
2. écrire les scripts de lecture
3. écrire les scripts d’écriture / lifecycle
4. ajouter la réconciliation
5. préciser les cas limites

Quand un nouveau script apparaît, on l’ajoute d’abord ici, puis seulement après dans l’implémentation.
