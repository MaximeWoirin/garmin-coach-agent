---
name: create-plan-session
description: Use after create-plan-draft to add each individual training session to the weekly plan.
---

# create-plan-session

## Quand l'utiliser

- Après avoir créé le plan avec `create-plan-draft`
- Pour chaque séance de la semaine (une par appel)
- Pour ajouter une séance de rattrapage ou de remplacement

## Commande

```bash
python -m garmin_coach.create_plan_session \
  --plan-id N \
  --planned-date YYYY-MM-DD \
  --activity-type TYPE \
  --duration-min N \
  [--intensity INTENSITY] \
  [--target-hr-low N] [--target-hr-high N] \
  [--target-pace-sec-per-km N] \
  [--target-rpe N] \
  [--notes "..."] \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--plan-id` | Oui | ID du plan parent |
| `--planned-date` | Oui | Date de la séance (YYYY-MM-DD) |
| `--activity-type` | Oui | Type (`running`, `cycling`, `swimming`, `strength`, etc.) |
| `--duration-min` | Oui | Durée cible en minutes |
| `--intensity` | Non | `easy`, `moderate`, `hard`, `race` |
| `--target-hr-low/high` | Non | Zone FC cible |
| `--target-pace-sec-per-km` | Non | Allure cible (ex: 360 = 6min/km) |
| `--target-rpe` | Non | Perception d'effort 1-10 |
| `--notes` | Non | Description de la séance |

## Sortie

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7,
  "session_status": "draft"
}
```

## Bonnes pratiques

- Toujours inclure `--notes` avec une description claire (l'utilisateur la verra dans Garmin)
- Préférer des cibles FC aux allures pour les débutants
- Vérifier la cohérence des dates avec `--week-start`/`--week-end` du plan
