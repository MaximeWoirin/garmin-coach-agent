# TOOLS.md — Garmin Coach Agent

Scripts disponibles via `python -m garmin_coach.<module>`. Pour chaque script, un skill associé est dans `agent/skills/`.

## Données Garmin

| Script | Module | Skill | Usage |
|---|---|---|---|
| `auth-garmin` | `auth_garmin` | [auth-garmin](skills/auth-garmin/SKILL.md) | Authentification Garmin Connect (premier démarrage ou token expiré) |
| `sync-garmin` | `sync_garmin` | [sync-garmin](skills/sync-garmin/SKILL.md) | Sync des activités et métriques depuis Garmin |
| `get-activities` | `get_activities` | [get-activities](skills/get-activities/SKILL.md) | Lecture des activités sur une période |
| `get-fitness-state` | `get_fitness_state` | [get-fitness-state](skills/get-fitness-state/SKILL.md) | État de forme (HRV, FC repos, sommeil, body battery) |

## Objectifs

| Script | Module | Skill | Usage |
|---|---|---|---|
| `get-goals` | `get_goals` | [get-goals](skills/get-goals/SKILL.md) | Lecture des objectifs actifs |
| `create-goal` | `create_goal` | _(à venir)_ | ⚠️ Module Python non encore créé |

## Contraintes

| Script | Module | Skill | Usage |
|---|---|---|---|
| `get-constraints` | `get_constraints` | [get-constraints](skills/get-constraints/SKILL.md) | Lecture des contraintes actives |
| `create-constraint` | `create_constraint` | [create-constraint](skills/create-constraint/SKILL.md) | Ajout d'une contrainte (blessure, indispo, préférence) |
| `set-constraint-status` | `set_constraint_status` | [set-constraint-status](skills/set-constraint-status/SKILL.md) | Changer le statut d'une contrainte |
| `delete-constraint` | `delete_constraint` | [delete-constraint](skills/delete-constraint/SKILL.md) | Supprimer une contrainte créée par erreur |

## Plans d'entraînement

| Script | Module | Skill | Usage |
|---|---|---|---|
| `get-current-plan` | `get_current_plan` | [get-current-plan](skills/get-current-plan/SKILL.md) | Lire le plan actif |
| `create-plan-draft` | `create_plan_draft` | [create-plan-draft](skills/create-plan-draft/SKILL.md) | Créer la coquille d'un nouveau plan |
| `create-plan-session` | `create_plan_session` | [create-plan-session](skills/create-plan-session/SKILL.md) | Ajouter une séance à un plan |
| `set-plan-status` | `set_plan_status` | [set-plan-status](skills/set-plan-status/SKILL.md) | Valider, activer ou archiver un plan |
| `set-plan-session-status` | `set_plan_session_status` | [set-plan-session-status](skills/set-plan-session-status/SKILL.md) | Marquer une séance done/skipped/exported |
| `delete-plan-session` | `delete_plan_session` | [delete-plan-session](skills/delete-plan-session/SKILL.md) | Supprimer une séance créée par erreur |
| `export-plan-garmin` | `export_plan_garmin` | [export-plan-garmin](skills/export-plan-garmin/SKILL.md) | Pousser le plan vers Garmin Connect |

## Flags communs

| Flag | Effet |
|---|---|
| `--dry-run` | Simule sans écrire ni appeler l'API |
| `--limit N` | Limite le nombre de résultats |
| `--start` / `--end` | Plage de dates (format `YYYY-MM-DD`) |
| `--plan-id N` | Cible un plan spécifique |
| `--session-id N` | Cible une séance spécifique |
