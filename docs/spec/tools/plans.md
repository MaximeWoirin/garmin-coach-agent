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
- workflow propre de remplacement d’une séance déjà exportée

## Backbone minimal

Le backbone V0 du bloc plans repose sur ces scripts :

- `create-plan-draft` : crée un plan local avec ses métadonnées et ses séances
- `sync-garmin` : récupère le réel et réconcilie le plan avec les activités importées
- `export-plan-garmin` : pousse un plan local vers Garmin

## Modèle de travail

- un **plan** porte les métadonnées : objectif, semaine, notes, contexte
- les **plan_sessions** portent les séances associées au plan
- le draft existe localement avant export
- la validation locale ne vaut pas export immédiat complet
- Garmin ne reçoit idéalement que les séances proches de l’exécution
- Garmin ne devient source de vérité que pour le réalisé

## Scripts envisagés

- `create-plan-draft`
- `create-plan-session`
- `update-plan-session`
- `replace-plan-session`
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

## Workflow recommandé

- `draft` = construction / édition locale
- `active` + sessions `proposed` = validation locale
- `exported` = publication Garmin, idéalement seulement pour l’horizon court
- `done` / `skipped` / `canceled` = état final ou de remplacement

Conséquence importante :
- une séance `proposed` doit rester éditable
- une séance `exported` doit être remplacée proprement, pas mutée librement

## Questions ouvertes

- quelle part de la réconciliation doit vivre dans le `sync-garmin` vs dans une logique réutilisable interne ?
- faut-il modéliser explicitement `superseded` ou réutiliser `canceled` pour une séance remplacée ?
