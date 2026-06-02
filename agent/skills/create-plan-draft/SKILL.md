---
name: create-plan-draft
description: Use when starting the weekly planning cycle to create a new training plan shell before adding sessions.
---

# create-plan-draft

## Quand l'utiliser

- Chaque semaine, pour créer la coquille du nouveau plan
- Toujours après avoir lu les objectifs (`get-goals`) et les contraintes (`get-constraints`)
- Jamais sans avoir vérifié l'état de forme (`get-fitness-state`) et les activités récentes (`get-activities`)

## Ordre d'appel recommandé

1. `get-goals` → identifier l'objectif principal
2. `get-constraints` → identifier les limites de la semaine
3. `get-fitness-state` → évaluer la forme
4. `get-activities` → voir la charge récente
5. **`create-plan-draft`** → créer le plan
6. `create-plan-session` × N → ajouter les séances

## Commande

```bash
python -m garmin_coach.create_plan_draft \
  --week-start YYYY-MM-DD \
  --week-end YYYY-MM-DD \
  [--goal-id N] \
  [--notes "..."] \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--week-start` | Oui | Lundi de la semaine |
| `--week-end` | Oui | Dimanche de la semaine |
| `--goal-id` | Non | Objectif associé |
| `--notes` | Non | Contexte libre |
| `--dry-run` | Non | Simule sans écrire |

## Sortie

```json
{
  "status": "success",
  "plan_id": 42,
  "week_start": "2025-01-13",
  "week_end": "2025-01-19",
  "plan_status": "draft"
}
```

Utiliser le `plan_id` retourné pour tous les appels `create-plan-session` suivants.
