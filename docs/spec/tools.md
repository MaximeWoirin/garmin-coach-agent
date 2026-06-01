# Outils — structure fonctionnelle

## But

Cette page sert d’index stable pour l’architecture des outils.

Le principe est simple :
- on découpe le système par **bloc métier**
- on décrit chaque bloc avec le même cadre
- on ajoute les scripts petit à petit sans casser la vue d’ensemble
- l’agent consomme des outils génériques, pas des scripts “coach” spécialisés

## Navigation

- [`activities.md`](tools/activities.md)
- [`metrics.md`](tools/metrics.md)
- [`constraints.md`](tools/constraints.md)
- [`plans.md`](tools/plans.md)

## Blocs métier

| Bloc | Rôle | État |
|---|---|---|
| Activités | Séances réelles, import Garmin, lecture, réconciliation | à détailler |
| Métriques physiologiques | Daily metrics, readiness, lecture, synchro | presque complet |
| Contraintes | Contraintes de vie / training / santé / dispo | lecture seule pour l’instant |
| Plans | Plan hebdo, séances planifiées, export Garmin, revue | à structurer |

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

### Activités

- **Existant** : `sync-garmin`, `get-activities`
- **Manquant** : réconciliation Garmin, matching plan ↔ activité
- **Dépendances** : Garmin source, SQLite, `plan_activity_matches`

### Métriques physiologiques

- **Existant** : `sync-garmin`, `get-fitness-state`
- **Manquant** : rien de bloquant en V0
- **Dépendances** : Garmin source, SQLite, `daily_metrics`

### Contraintes

- **Existant** : `get-constraints`
- **Manquant** : création, suppression, changement de statut
- **Dépendances** : mémoire agent pour le durable, SQLite pour l’état actif/historique

### Plans

- **Existant** : schéma DB (`training_blocks`, `training_plans`, `plan_sessions`, `plan_reviews`)
- **Manquant** : lecture du plan courant, création/suppression de séances, changement de statut, export Garmin
- **Dépendances** : objectifs, contraintes, activités, métriques physiologiques, historique du plan

## Authentification Garmin

- `auth-garmin` fait partie du socle à implémenter
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
