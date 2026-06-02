---
name: get-activities
description: Use when reviewing completed workouts, analyzing training load, or preparing the weekly coaching debrief.
---

# get-activities

## Quand l'utiliser

- Bilan de semaine : voir ce qui a été réalisé vs planifié
- Analyse de la charge avant de proposer un nouveau plan
- L'utilisateur mentionne une séance récente à analyser

## Commande

```bash
python -m garmin_coach.get_activities [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--limit N]
```

## Paramètres clés

| Paramètre | Description |
|---|---|
| `--start` / `--end` | Plage de dates (défaut : 7 derniers jours) |
| `--limit` | Nombre max d'activités retournées |

## Sortie (par activité)

```json
{
  "activity_id": "...",
  "activity_date": "2025-01-15",
  "activity_type": "running",
  "duration_seconds": 3600,
  "distance_meters": 10000,
  "avg_hr": 145,
  "max_hr": 168,
  "avg_pace_sec_per_km": 360,
  "training_load": 85,
  "notes": "..."
}
```

## Exemple typique

```bash
# Bilan de la semaine écoulée
python -m garmin_coach.get_activities --start 2025-01-13 --end 2025-01-19
```
