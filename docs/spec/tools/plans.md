# Plans

## Rôle

Gérer le plan d’entraînement vivant : blocs, semaines, séances, revue, export Garmin.

## Existant

- schéma de base de données déjà cadré
- `training_blocks`
- `training_plans`
- `plan_sessions`
- `plan_reviews`
- `plan_activity_matches`

## Ce qui manque

- lecture du plan courant
- création d’un plan hebdomadaire en draft
- mise à jour / adaptation du plan
- export vers Garmin
- réconciliation plan ↔ réalisé
- revue structurée du plan

## Backbone minimal

Le backbone V0 du bloc plans repose sur ces scripts :

- `create-plan-draft` : crée un plan local avec ses métadonnées et ses séances
- `sync-garmin` : récupère le réel et réconcilie le plan avec les activités importées
- `export-plan-garmin` : pousse un plan local vers Garmin

## Modèle de travail

- un **plan** porte les métadonnées : objectif, semaine, notes, contexte
- les **plan_sessions** portent les séances associées au plan
- le draft existe localement avant export
- Garmin ne devient source de vérité que pour le réalisé

## Scripts envisagés

- `create-plan-draft`
- `create-plan-session`
- `delete-plan-session`
- `get-current-plan`
- `set-plan-status`
- `set-plan-session-status`
- `export-plan-garmin`

## Dépendances

- objectifs
- contraintes
- activités réelles
- métriques physiologiques
- historique des plans
- métadonnées de plan

## Questions ouvertes

- quelle part de la réconciliation doit vivre dans le `sync-garmin` vs dans une logique réutilisable interne ?
