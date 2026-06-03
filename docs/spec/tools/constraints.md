# Contraintes

## Rôle

Garder la trace des contraintes d’entraînement et de vie qui influencent le plan.

## Existant

- `get-constraints`
- `create-constraint`
- `delete-constraint`
- `set-constraint-status`
- liage optionnel à un objectif via `goal_id`

## Ce qui manque

- éventuelle édition d’une contrainte existante sans delete + recreate
- règles de déduplication / consolidation si plusieurs contraintes se recouvrent
- normalisation plus poussée si le texte libre devient insuffisant

## Backbone minimal

Le backbone V1 du bloc contraintes repose sur ces scripts :

- `get-constraints`
- `create-constraint`
- `set-constraint-status`
- `delete-constraint`

## Dépendances

- table `constraints`
- table `training_goals`
- mémoire agent pour les éléments stables

## Questions ouvertes

- le script d’écriture doit-il accepter du texte libre + normalisation, ou des champs déjà structurés ?
