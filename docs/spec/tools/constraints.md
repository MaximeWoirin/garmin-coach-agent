# Contraintes

## Rôle

Garder la trace des contraintes d’entraînement et de vie qui influencent le plan.

## Existant

- `get-constraints`

## Ce qui manque

- création
- mise à jour
- archivage / résolution
- éventuel liage à un objectif

## Scripts envisagés

- `create-constraint`
- `update-constraint`
- `archive-constraint`
- `resolve-constraint`

## Dépendances

- table `constraints`
- table `training_goals`
- mémoire agent pour les éléments stables

## Questions ouvertes

- le script d’écriture doit-il accepter du texte libre + normalisation, ou des champs déjà structurés ?
- doit-on séparer résolution et archivage ?
