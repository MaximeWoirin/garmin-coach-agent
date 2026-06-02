---
name: get-current-plan
description: Use when reviewing the current week's training plan, checking session statuses, or before modifying a plan.
---

# get-current-plan

## Quand l'utiliser

- En début de session pour voir le plan actif
- Avant d'ajouter, modifier ou supprimer une séance
- Quand l'utilisateur demande "c'est quoi mon programme cette semaine ?"
- Avant l'export Garmin pour vérifier que le plan est complet

## Commande

```bash
python -m garmin_coach.get_current_plan [--plan-id N] [--session-id N]
```

## Paramètres clés

| Paramètre | Description |
|---|---|
| `--plan-id` | Récupérer un plan spécifique (défaut : plan actif) |
| `--session-id` | Récupérer une séance spécifique |

## Sortie

```json
{
  "plan_id": 42,
  "week_start": "2025-01-13",
  "week_end": "2025-01-19",
  "status": "active",
  "sessions": [
    {
      "session_id": 7,
      "planned_date": "2025-01-14",
      "activity_type": "running",
      "duration_min": 60,
      "intensity": "easy",
      "status": "proposed",
      "notes": "Endurance fondamentale Z2"
    }
  ]
}
```

## Statuts de plan

| Statut | Signification |
|---|---|
| `draft` | Plan en cours de construction |
| `active` | Plan validé et en cours |
| `exported` | Exporté vers Garmin Connect |
| `archived` | Semaine terminée |
