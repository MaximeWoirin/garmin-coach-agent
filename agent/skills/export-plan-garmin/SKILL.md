---
name: export-plan-garmin
description: Use to export plan sessions to Garmin Connect on a short horizon.
---

# export-plan-garmin

## Quand l'utiliser

- Après validation locale d'un plan (`draft -> active`)
- Pour pousser seulement l'horizon court vers Garmin
- Quand l'utilisateur veut voir les prochaines séances sur Garmin

## Règles de workflow

- L'export est piloté au niveau **session**.
- Par défaut, seules les séances `proposed` sont exportables.
- Les séances `draft` ne partent pas.
- Les séances `exported` ne repartent pas, sauf `--force`.
- `set-plan-status` ne publie pas sur Garmin ; il valide seulement le cycle local du plan.

## Commande

```bash
python -m garmin_coach.export_plan_garmin \
  (--plan-id N | --week-start YYYY-MM-DD) \
  [--start-date YYYY-MM-DD] \
  [--end-date YYYY-MM-DD] \
  [--days-ahead N] \
  [--dry-run] \
  [--force]
```

## Contrat réel

- Il faut fournir `--plan-id` **ou** `--week-start`.
- `--start-date`, `--end-date`, `--days-ahead` bornent l'horizon d'export.
- `--force` permet une réexport explicite des séances déjà `exported`.
- La sortie contient `sessions_seen`, `sessions_exported`, `sessions_skipped`, `sessions_ignored`, `sessions_failed`, `garmin_event_ids`.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "week_start": "2026-06-16",
  "week_end": "2026-06-22",
  "sessions_seen": 5,
  "sessions_exported": 2,
  "sessions_skipped": 2,
  "sessions_ignored": 1,
  "sessions_failed": 0,
  "garmin_event_ids": ["dry-run-7", "dry-run-8"]
}
```
