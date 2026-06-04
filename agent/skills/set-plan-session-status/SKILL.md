---
name: set-plan-session-status
description: Use to move one session through its local/session publication lifecycle.
---

# set-plan-session-status

## Quand l'utiliser

- `draft -> proposed` pour marquer une séance prête à publication
- `proposed -> exported` après export Garmin
- `exported -> done` quand la séance est réalisée
- `proposed` / `exported` -> `skipped` ou `canceled` selon le cas

## Commande

```bash
<EXEC_DIR>/set-plan-session-status \
  --plan-id N \
  --session-id N \
  --status draft|proposed|exported|done|skipped|canceled \
  [--dry-run]
```

## Transitions valides

- `draft -> proposed|canceled`
- `proposed -> exported|skipped|canceled`
- `exported -> done|skipped|canceled`

## Contrat réel

- Il n'existe pas de statut `missed`.
- La sortie renvoie `session_status`, pas `old_status` / `new_status`.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7,
  "session_status": "done"
}
```
