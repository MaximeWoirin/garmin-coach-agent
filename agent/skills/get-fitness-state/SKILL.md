---
name: get-fitness-state
description: Use when assessing current fatigue, readiness, or fitness level before building or adjusting a training plan.
---

# get-fitness-state

## Quand l'utiliser

- Avant de créer un nouveau plan (estimer la forme de départ)
- Si l'utilisateur mentionne fatigue, récup difficile, ou pics de forme
- Contrôle hebdomadaire de la charge accumulée
- Après une période de maladie ou absence

## Commande

```bash
python -m garmin_coach.get_fitness_state [--start YYYY-MM-DD] [--end YYYY-MM-DD]
```

## Paramètres clés

| Paramètre | Description |
|---|---|
| `--start` / `--end` | Plage d'analyse (défaut : 7 derniers jours) |

## Sortie (par jour)

```json
{
  "date": "2025-01-15",
  "resting_hr": 52,
  "hrv": 68,
  "sleep_score": 82,
  "body_battery": 74,
  "stress_avg": 28,
  "steps": 9500
}
```

## Interprétation

| Signal | Faible → Attention | Élevé → Bon signe |
|---|---|---|
| HRV | <50 | >70 |
| Body Battery matin | <30 | >80 |
| Sleep score | <60 | >85 |
| FC repos | Hausse persistante | Stable/en baisse |

## Exemple typique

```bash
# État de forme avant planification du lundi
python -m garmin_coach.get_fitness_state
```
