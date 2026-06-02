---
name: set-constraint-status
description: Use when a constraint changes state — resolved after healing, paused temporarily, or reactivated.
---

# set-constraint-status

## Quand l'utiliser

- L'utilisateur annonce qu'une blessure est guérie → `resolved`
- Une contrainte est suspendue temporairement (ex: vacances reportées) → `paused`
- Une contrainte résolue réapparaît → `active`
- Mise à jour de routine après qu'une période de contrainte prend fin

## Commande

```bash
python -m garmin_coach.set_constraint_status \
  --constraint-id N \
  --status STATUS \
  [--dry-run]
```

## Statuts valides

| Statut | Quand l'utiliser |
|---|---|
| `active` | La contrainte s'applique maintenant |
| `paused` | Temporairement suspendue |
| `resolved` | Définitivement levée (garde l'historique) |

## Sortie

```json
{
  "status": "success",
  "constraint_id": 5,
  "old_status": "active",
  "new_status": "resolved"
}
```

## Exemple typique

```bash
# L'utilisateur dit "mon genou va mieux, je peux reprendre la course"
python -m garmin_coach.set_constraint_status --constraint-id 5 --status resolved
```

## À faire ensuite

Après avoir résolu une contrainte de santé, revoir le plan en cours si les séances avaient été adaptées.
