---
name: set-plan-status
description: Use to transition a plan through its lifecycle — validate a draft, activate it, or archive a finished week.
---

# set-plan-status

## Quand l'utiliser

- Après avoir terminé la construction d'un plan (`draft` → `active`)
- Avant l'export Garmin (le plan doit être `active`)
- En fin de semaine pour archiver (`active` → `archived`)

## Commande

```bash
python -m garmin_coach.set_plan_status \
  --plan-id N \
  --status STATUS \
  [--cascade-sessions] \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--plan-id` | Oui | ID du plan |
| `--status` | Oui | Nouveau statut |
| `--cascade-sessions` | Non | Propage le statut aux séances (ex: `draft`→`proposed`) |

## Transitions valides

```
draft → active      (validation du plan)
active → exported   (après export Garmin)
active → archived   (fin de semaine sans export)
exported → archived (fin de semaine après export)
```

## Sortie

```json
{
  "status": "success",
  "plan_id": 42,
  "plan_status": "active",
  "session_status_changes": [
    {"session_id": 7, "old_status": "draft", "new_status": "proposed"}
  ]
}
```

## Exemple typique

```bash
# Valider le plan et passer les séances en "proposed"
python -m garmin_coach.set_plan_status --plan-id 42 --status active --cascade-sessions
```
