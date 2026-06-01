# Activités

## Rôle

Gérer les séances réelles importées depuis Garmin.

## Existant

- `sync-garmin`
- `get-activities`

## Ce qui manque probablement

- réconciliation Garmin
- matching entre activité réelle et séance planifiée
- gestion des doublons et des corrections tardives

## Scripts envisagés

- `sync-garmin`

## Dépendances

- table `activities`
- table `plan_activity_matches`
- import Garmin

## Questions ouvertes

- la réconciliation doit-elle être automatique dans `sync-garmin` ou exposée aussi en logique interne réutilisable ?
