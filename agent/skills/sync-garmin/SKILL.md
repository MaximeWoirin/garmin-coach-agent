---
name: sync-garmin
description: Use when Garmin data may be stale, before reading activities or metrics, or when the user reports missing workouts.
---

# sync-garmin

## Quand l'utiliser

- Au début d'une session hebdomadaire de planification
- Quand l'utilisateur mentionne une activité récente non visible
- Quand `get-activities` ou `get-fitness-state` renvoient des données obsolètes
- Jamais en boucle : une seule sync par session suffit

## Commande

```bash
python -m garmin_coach.sync_garmin [--week-start YYYY-MM-DD] [--week-end YYYY-MM-DD] [--start YYYY-MM-DD] [--end YYYY-MM-DD]
```

## Paramètres clés

| Paramètre | Description |
|---|---|
| `--week-start` / `--week-end` | Sync d'une semaine précise |
| `--start` / `--end` | Plage de dates libre |
| _(aucun)_ | Sync de la semaine courante |

## Sortie

```json
{
  "status": "success",
  "synced_days": 7,
  "activities_imported": 3,
  "warnings": []
}
```

## Exemple typique

```bash
# Sync de la semaine courante avant de planifier
python -m garmin_coach.sync_garmin
```
