---
name: delete-plan-session
description: Use to delete a non-exported, non-completed plan session.
---

# delete-plan-session

## Quand l'utiliser

- Séance créée par erreur
- Remplacement d'une séance encore éditable
- Adaptation locale avant export Garmin

## Ne pas utiliser

- Pour une séance déjà `exported`
- Pour une séance déjà `done`

## Commande

```bash
python -m garmin_coach.delete_plan_session \
  --plan-id N \
  --session-id N \
  [--dry-run]
```

## Contrat réel

- Le script refuse explicitement les séances `exported` et `done`.
- Les séances `draft`, `proposed`, `skipped`, `canceled` restent supprimables.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7
}
```
