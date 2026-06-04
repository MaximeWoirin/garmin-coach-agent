---
name: create-goal
description: Use when the user defines a new training objective or a target event that must become structured goal data.
---

# create-goal

## Quand l'utiliser

- Nouveau grand objectif sportif
- Course cible à enregistrer
- Repriorisation explicite d'un objectif qui doit devenir un nouvel enregistrement

## Commande

```bash
<EXEC_DIR>/create-goal \
  --primary-goal "..." \
  [--goal-code CODE] \
  [--priority low|medium|high] \
  [--horizon-date YYYY-MM-DD] \
  [--target-event-name "..."] \
  [--target-event-date YYYY-MM-DD] \
  [--target-event-priority low|medium|high] \
  [--status active|archived|completed|canceled] \
  [--raw-text "..."] \
  [--metadata-json '{"k":"v"}'] \
  [--dry-run]
```

## Points importants

- `--primary-goal` est requis.
- `--goal-code` doit être unique s'il est fourni.
- `--metadata-json` doit être du JSON valide.
- Les dates sont attendues en `YYYY-MM-DD`.

## Sortie typique

```json
{
  "status": "success",
  "goal_id": 3,
  "goal_status": "active"
}
```
