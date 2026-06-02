---
name: get-goals
description: Use before building any training plan or when the user asks to review their current objectives.
---

# get-goals

## Quand l'utiliser

- Toujours avant de créer un plan (`create-plan-draft`)
- Quand l'utilisateur mentionne un objectif ou une course cible
- Pour vérifier si un objectif est encore actif ou a changé de priorité

## Commande

```bash
python -m garmin_coach.get_goals [--plan-id N] [--goal-id N] [--limit N]
```

## Paramètres clés

| Paramètre | Description |
|---|---|
| `--plan-id` | Filtrer les objectifs d'un plan spécifique |
| `--goal-id` | Récupérer un objectif précis |
| `--limit` | Nombre max de résultats |

## Sortie (par objectif)

```json
{
  "goal_id": 1,
  "goal_code": "marathon-2025",
  "primary_goal": "Finir le marathon de Paris en moins de 4h",
  "priority": 1,
  "horizon_date": "2025-04-13",
  "target_event_name": "Marathon de Paris",
  "target_event_date": "2025-04-13",
  "status": "active"
}
```

## À noter

Les objectifs sont en base de données (pas dans `USER.md`). C'est la source de vérité.  
Si l'utilisateur exprime un nouvel objectif → utiliser `create-goal` (⚠️ script à venir).
