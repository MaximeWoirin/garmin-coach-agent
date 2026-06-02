---
name: get-fitness-state
description: Use to read daily metrics on an explicit date range before planning or adaptation.
---

# get-fitness-state

## Quand l'utiliser

- Avant de construire une semaine
- Après fatigue, maladie, baisse de forme
- Pour inspecter la tendance récente

## Commande

```bash
python -m garmin_coach.get_fitness_state \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD \
  [--limit N]
```

## Contrat réel

- `--start` et `--end` sont requis.
- `--limit` existe vraiment.
- La sortie contient `period`, `daily_metrics`, `summary`.

## Sortie typique

```json
{
  "status": "success",
  "period": {"start": "2026-06-01", "end": "2026-06-08"},
  "daily_metrics": [],
  "summary": {
    "days": 0,
    "signal": "no_data"
  }
}
```
