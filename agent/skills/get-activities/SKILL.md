---
name: get-activities
description: Use to read imported Garmin activities on an explicit date range.
---

# get-activities

## Quand l'utiliser

- Bilan d'entraînement
- Analyse de charge récente
- Vérification qu'une activité a bien été synchronisée

## Commande

```bash
<EXEC_DIR>/get-activities \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD \
  [--limit N] \
  [--activity-type TYPE]
```

## Contrat réel

- `--start` et `--end` sont requis.
- `--activity-type` filtre côté lecture.
- La sortie contient `period`, `activities`, `summary`.

## Sortie typique

```json
{
  "status": "success",
  "period": {"start": "2026-06-01", "end": "2026-06-08"},
  "activities": [],
  "summary": {
    "count": 0,
    "total_duration_min": 0,
    "total_distance_km": 0.0,
    "total_calories_kcal": 0
  }
}
```
