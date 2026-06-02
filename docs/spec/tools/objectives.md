# Objectifs

## Rôle

Gérer les objectifs d’entraînement moyen terme qui donnent le cap au coaching :
compétition cible, défi personnel, horizon de progression, niveau d’ambition.

## Existant

- table `training_goals`
- scripts `get-goals` et `create-goal`
- liaison possible avec les contraintes (`constraints.goal_id`)
- liaison possible avec les blocs d’entraînement (`training_blocks.goal_id`)

## Ce qui manque

- archivage / fermeture explicite d’un objectif devenu obsolète
- éventuelle mise à jour d’un objectif existant si on veut éviter le delete + recreate
- règles de coexistence entre plusieurs objectifs actifs

## Backbone minimal

Le backbone V0 du bloc objectifs repose sur ces scripts :

- `get-goals` : lire les objectifs actifs ou archivés
- `create-goal` : enregistrer un nouvel objectif structuré pour l’agent et la planification

## Modèle de travail

- un **objectif** exprime une direction moyen terme, pas un plan hebdomadaire
- l’objectif doit rester assez stable pour guider plusieurs semaines
- un objectif peut exister sans événement cible précis
- la formulation utilisateur brute doit rester disponible via `raw_text`
- la normalisation doit rester légère : on stocke ce qu’on sait sans inventer de structure inutile

## Scripts envisagés

- `get-goals`
- `create-goal`
- plus tard éventuellement `set-goal-status`
- plus tard éventuellement `update-goal`

## Dépendances

- base SQLite (`training_goals`)
- contraintes éventuellement rattachées via `goal_id`
- blocs et plans d’entraînement qui se calent sur l’objectif courant
- mémoire agent pour le profil stable, mais pas pour l’état opérationnel des objectifs

## Questions ouvertes

- faut-il autoriser plusieurs objectifs `active` en parallèle ou un seul objectif principal ?
- faut-il distinguer priorité d’objectif et priorité d’événement cible ?
- faut-il ajouter un champ normalisé de type d’objectif (`race`, `performance`, `consistency`, etc.) ou garder `primary_goal` libre en V0 ?
- faut-il un vrai `set-goal-status` maintenant, ou le couple `create-goal` + future archive suffit-il ?
