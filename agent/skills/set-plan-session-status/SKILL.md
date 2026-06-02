---
name: set-plan-session-status
description: Use to update the status of an individual session — marking it done, skipped, or exported.
---

# set-plan-session-status

## Quand l'utiliser

- L'utilisateur confirme avoir réalisé une séance → `done`
- L'utilisateur annule une séance → `skipped`
- Après export d'une séance individuelle → `exported`
- Réconciliation avec les activités Garmin réelles

## Commande

```bash
python -m garmin_coach.set_plan_session_status \
  --plan-id N \
  --session-id N \
  --status STATUS \
  [--dry-run]
```

## Statuts valides

| Statut | Quand l'utiliser |
|---|---|
| `draft` | Séance en construction |
| `proposed` | Séance validée, en attente de réalisation |
| `exported` | Envoyée vers Garmin Connect |
| `done` | Réalisée (avec ou sans activité liée) |
| `skipped` | Sautée volontairement |
| `missed` | Non réalisée sans annulation explicite |

## Sortie

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7,
  "old_status": "proposed",
  "new_status": "done"
}
```

## Exemple typique

```bash
# Marquer une séance comme réalisée après retour de l'utilisateur
python -m garmin_coach.set_plan_session_status --plan-id 42 --session-id 7 --status done
```
