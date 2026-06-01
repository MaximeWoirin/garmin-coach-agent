# Contraintes

## Rôle

Garder la trace des contraintes d’entraînement et de vie qui influencent le plan.

## Existant

- `get-constraints`

## Ce qui manque

- création
- suppression
- changement de statut
- éventuel liage à un objectif

## Scripts envisagés

- `create-constraint`
- `delete-constraint`
- `set-constraint-status`

## Dépendances

- table `constraints`
- table `training_goals`
- mémoire agent pour les éléments stables

## Questions ouvertes

- le script d’écriture doit-il accepter du texte libre + normalisation, ou des champs déjà structurés ?
