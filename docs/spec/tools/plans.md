# Plans

## Rôle

Gérer le plan d'entraînement vivant : blocs, semaines, séances, revue, export Garmin.

## Existant

- schéma de base de données déjà cadré
- `training_blocks`
- `training_plans`
- `plan_sessions`
- `plan_reviews`
- `plan_activity_matches`
- `get-current-plan`
- `create-plan-draft`
- `create-plan-session`
- `delete-plan-session`
- `set-plan-status`
- `set-plan-session-status`
- `export-plan-garmin`

## Backbone minimal

Le backbone V1 du bloc plans repose sur ces scripts :

- `get-current-plan` : lit le plan courant ou un plan ciblé
- `create-plan-draft` : crée un plan local avec ses métadonnées et ses séances
- `create-plan-session` : ajoute une séance à un plan
- `delete-plan-session` : supprime une séance locale (draft ou proposed)
- `set-plan-status` : validation locale ou clôture du plan
- `set-plan-session-status` : changement granulaire de statut de séance
- `export-plan-garmin` : pousse les séances `proposed` vers Garmin (export progressif)
- `sync-garmin` : récupère le réel et réconcilie le plan avec les activités importées

## Modèle de travail

- un **plan** porte les métadonnées : objectif, semaine, notes, contexte
- les **plan_sessions** portent les séances associées au plan
- le draft existe localement avant export
- la validation locale ne vaut pas export immédiat complet
- Garmin ne reçoit idéalement que les séances proches de l'exécution
- Garmin ne devient source de vérité que pour le réalisé
- la publication Garmin est suivie **au niveau session** (proposed → exported)
- le statut de plan ne porte pas l'état de publication

## Workflow recommandé

- `draft` = construction / édition locale
- `active` = plan validé localement (sessions passent à `proposed`)
- `archived` = plan clos
- `proposed` → `exported` = publication Garmin progressive, horizon court
- `done` / `skipped` / `canceled` = état final

Conséquence importante :
- une séance `proposed` reste éditable (delete + recreate)
- une séance `exported` est verrouillée
- l'adaptation se fait **avant export**, grâce au mode progressif / last minute

## Édition de séances (V1)

L'adaptation passe par :
- `delete-plan-session` pour supprimer une séance `draft` ou `proposed`
- `create-plan-session` pour recréer une nouvelle séance

Pas de `update-plan-session` ni de `replace-plan-session` en V1.

## Dépendances

- objectifs
- contraintes
- activités réelles
- métriques physiologiques
- historique des plans
- métadonnées de plan
