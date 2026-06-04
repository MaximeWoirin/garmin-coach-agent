---
name: sync-garmin
description: Use to import Garmin activities and daily metrics into the local database.
---

# sync-garmin

## Quand l'utiliser

- Avant lecture des activités récentes
- Avant lecture des métriques de forme
- Quand l'utilisateur dit qu'une activité Garmin manque

## Commande

```bash
<EXEC_DIR>/sync-garmin \
  [--start YYYY-MM-DD] \
  [--end YYYY-MM-DD] \
  [--lookback-days N]
```

## Contrat réel

- Les vrais flags sont `--start`, `--end`, `--lookback-days`.
- Il n'existe pas de `--week-start` / `--week-end`.
- Sans dates explicites, le script synchronise une fenêtre calculée depuis `lookback_days`.
- La sortie contient notamment `range_start`, `range_end`, `activities_*`, `daily_metrics_*`.

## Sortie typique

```json
{
  "status": "success",
  "source": "garmin",
  "range_start": "2026-06-01",
  "range_end": "2026-06-03",
  "activities_seen": 0,
  "activities_inserted": 0,
  "activities_updated": 0,
  "daily_metrics_seen": 0,
  "daily_metrics_upserted": 0,
  "reconciled_sessions": 0,
  "matched_activities": 0
}
```
