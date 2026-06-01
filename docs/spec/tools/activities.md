# Activités

## Rôle

Gérer les séances réelles importées depuis Garmin, et éventuellement les activités manuelles si on décide d’en supporter.

## Existant

- `sync-garmin`
- `get-activities`

## Ce qui manque probablement

- réconciliation Garmin
- matching entre activité réelle et séance planifiée
- gestion des doublons et des corrections tardives

## Scripts envisagés

- `reconcile-plan`
- `match-plan-activity`

## Dépendances

- table `activities`
- table `plan_activity_matches`
- import Garmin

## Questions ouvertes

- veut-on vraiment des activités manuelles en V0 ?
- la réconciliation doit-elle être automatique ou déclenchée par le cron ?
