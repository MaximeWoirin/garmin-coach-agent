# Activités

## Rôle

Gérer les séances réelles importées depuis Garmin.

## Existant

- `sync-garmin`
- `get-activities`

## Ce qui manque probablement

- matching plus fin entre activité réelle et séance planifiée
- gestion explicite des doublons et des corrections tardives
- éventuel rapport de réconciliation dédié si le snapshot de sync devient trop chargé

## Backbone minimal

Le backbone V1 du bloc activités repose sur ces scripts :

- `sync-garmin`
- `get-activities`

## Dépendances

- table `activities`
- table `plan_activity_matches`
- import Garmin

## Questions ouvertes

- la réconciliation doit-elle être automatique dans `sync-garmin` ou exposée aussi en logique interne réutilisable ?
