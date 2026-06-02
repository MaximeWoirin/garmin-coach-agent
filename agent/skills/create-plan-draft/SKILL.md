---
name: create-plan-draft
description: Use to create a local weekly plan shell before adding sessions.
---

# create-plan-draft

## Quand l'utiliser

- Début de construction d'une semaine
- Après lecture des objectifs / contraintes / forme
- Avant toute création de séance

## Commande

```bash
python -m garmin_coach.create_plan_draft \
  --week-start YYYY-MM-DD \
  --week-end YYYY-MM-DD \
  [--goal-id N] \
  [--block-id N] \
  [--title "..."] \
  [--notes "..."] \
  [--metadata-json '{"k":"v"}'] \
  [--sessions-json '[{"planned_date":"...","activity_type":"running","duration_min":45}]'] \
  [--dry-run]
```

## Contrat réel

- `--week-start` et `--week-end` sont requis.
- `--block-id` est vérifié en base si fourni.
- `--title` est injecté dans `metadata_json`.
- `--sessions-json` permet de créer des séances initiales directement.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "week_start": "2026-06-16",
  "week_end": "2026-06-22",
  "plan_status": "draft",
  "sessions_created": 2
}
```
