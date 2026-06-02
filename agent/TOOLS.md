# TOOLS.md — Garmin Coach Agent

Invocation canonique: `python -m garmin_coach.<module>`.

Les fichiers `bin/*` sont seulement des wrappers locaux. La doc agent doit toujours référencer les modules Python comme contrat public.

## Données Garmin

| Script | Module | Skill | Usage |
|---|---|---|---|
| `auth-garmin` | `auth_garmin` | [auth-garmin](skills/auth-garmin/SKILL.md) | Authentifier ou réutiliser un token Garmin Connect |
| `sync-garmin` | `sync_garmin` | [sync-garmin](skills/sync-garmin/SKILL.md) | Importer activités + métriques Garmin sur une plage |
| `get-activities` | `get_activities` | [get-activities](skills/get-activities/SKILL.md) | Lire les activités importées sur une période |
| `get-fitness-state` | `get_fitness_state` | [get-fitness-state](skills/get-fitness-state/SKILL.md) | Lire les métriques journalières de forme |

## Objectifs

| Script | Module | Skill | Usage |
|---|---|---|---|
| `get-goals` | `get_goals` | [get-goals](skills/get-goals/SKILL.md) | Lire les objectifs stockés en base |
| `create-goal` | `create_goal` | [create-goal](skills/create-goal/SKILL.md) | Créer un objectif d'entraînement |

## Contraintes

| Script | Module | Skill | Usage |
|---|---|---|---|
| `get-constraints` | `get_constraints` | [get-constraints](skills/get-constraints/SKILL.md) | Lire les contraintes filtrées par scope/statut |
| `create-constraint` | `create_constraint` | [create-constraint](skills/create-constraint/SKILL.md) | Créer une contrainte utilisateur |
| `set-constraint-status` | `set_constraint_status` | [set-constraint-status](skills/set-constraint-status/SKILL.md) | Passer une contrainte en `active` ou `inactive` |
| `delete-constraint` | `delete_constraint` | [delete-constraint](skills/delete-constraint/SKILL.md) | Supprimer une contrainte erronée |

## Plans d'entraînement

| Script | Module | Skill | Usage |
|---|---|---|---|
| `get-current-plan` | `get_current_plan` | [get-current-plan](skills/get-current-plan/SKILL.md) | Lire le plan courant ou un plan ciblé |
| `create-plan-draft` | `create_plan_draft` | [create-plan-draft](skills/create-plan-draft/SKILL.md) | Créer un plan local `draft` |
| `create-plan-session` | `create_plan_session` | [create-plan-session](skills/create-plan-session/SKILL.md) | Ajouter une séance à un plan |
| `set-plan-status` | `set_plan_status` | [set-plan-status](skills/set-plan-status/SKILL.md) | Valider localement un plan ou l'archiver |
| `set-plan-session-status` | `set_plan_session_status` | [set-plan-session-status](skills/set-plan-session-status/SKILL.md) | Changer le statut d'une séance |
| `delete-plan-session` | `delete_plan_session` | [delete-plan-session](skills/delete-plan-session/SKILL.md) | Supprimer une séance non exportée / non réalisée |
| `export-plan-garmin` | `export_plan_garmin` | [export-plan-garmin](skills/export-plan-garmin/SKILL.md) | Export progressif des séances vers Garmin |

## Règles de lecture des flags

Ne pas supposer qu'un flag est « commun » juste parce qu'il existe ailleurs.

- `--dry-run` existe sur les scripts mutateurs, pas sur les scripts de lecture.
- `--limit` existe seulement sur certains scripts de lecture (`get-goals`, `get-constraints`, `get-activities`, `get-fitness-state`).
- `--start` / `--end` existent sur `sync-garmin`, `get-activities`, `get-fitness-state`.
- `--week-start` existe sur `get-current-plan` et `export-plan-garmin`.
- `--plan-id` n'existe que sur les scripts qui ciblent explicitement un plan.

En cas de doute: relire le module Python correspondant, pas un autre skill.
