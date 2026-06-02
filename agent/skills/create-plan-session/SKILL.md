---
name: create-plan-session
description: Use after create-plan-draft to add one session to a plan.
---

# create-plan-session

## Quand l'utiliser

- Ajouter une séance à un plan existant
- Compléter un draft semaine par semaine
- Remplacer une séance non exportée via delete + create

## Commande

```bash
python -m garmin_coach.create_plan_session \
  --plan-id N \
  --planned-date YYYY-MM-DD \
  --activity-type TYPE \
  --duration-min N \
  [--planned-time HH:MM] \
  [--intensity TEXT] \
  [--target-hr-low N] \
  [--target-hr-high N] \
  [--target-pace-sec-per-km N] \
  [--target-rpe N] \
  [--status draft|proposed|exported|done|skipped|canceled] \
  [--tags-json '["tag"]'] \
  [--notes "..."] \
  [--workout-payload-json '{"workoutName":"..."}'] \
  [--dry-run]
```

## Points importants

- `--plan-id`, `--planned-date`, `--activity-type`, `--duration-min` sont requis.
- `--status` existe vraiment et vaut `draft` par défaut.
- `--workout-payload-json` permet de fournir un payload Garmin déjà préparé.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7,
  "session_status": "draft"
}
```
