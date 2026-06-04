---
name: set-plan-status
description: Use to move a plan through its local lifecycle only.
---

# set-plan-status

## Quand l'utiliser

- `draft -> active` pour valider localement une semaine
- `draft -> archived` pour abandonner un draft
- `active -> archived` pour clore la semaine

## Règle importante

Le statut du plan est **local**.

- Publication Garmin = statut de **session** (`proposed -> exported`)
- `PlanStatus.SENT` reste seulement un état legacy de compatibilité lecture / transition
- Le workflow cible normal est `draft`, `active`, `archived`

## Commande

```bash
<EXEC_DIR>/set-plan-status \
  --plan-id N \
  --status draft|active|sent|archived \
  [--cascade-sessions] \
  [--dry-run]
```

## Transitions valides

- `draft -> active|archived`
- `active -> archived`
- `sent -> active|archived` (compat legacy)

## Cascade sessions

- `draft -> active` avec `--cascade-sessions` fait `draft -> proposed` pour les séances draft
- `* -> archived` avec `--cascade-sessions` annule les séances `draft` / `proposed`

## Sortie typique

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
