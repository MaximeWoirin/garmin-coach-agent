---
name: get-constraints
description: Use before building a training plan, or when the user mentions an injury, travel, or any limitation affecting their training.
---

# get-constraints

## Quand l'utiliser

- Toujours avant de créer un plan (`create-plan-draft`)
- Quand l'utilisateur mentionne une blessure, vacances, surcharge de travail
- Pour vérifier quelles contraintes sont encore actives
- Si une séance semble incompatible avec la réalité de l'utilisateur

## Commande

```bash
python -m garmin_coach.get_constraints [--plan-id N] [--session-id N] [--limit N]
```

## Paramètres clés

| Paramètre | Description |
|---|---|
| `--plan-id` | Contraintes d'un plan spécifique |
| `--session-id` | Contraintes d'une séance spécifique |
| `--limit` | Nombre max de résultats |

## Sortie (par contrainte)

```json
{
  "constraint_id": 3,
  "type": "health",
  "severity": "medium",
  "status": "active",
  "scope": "training",
  "start_date": "2025-01-10",
  "end_date": "2025-01-24",
  "raw_text": "Douleur genou gauche, éviter la course",
  "tags": ["knee", "no-running"]
}
```

## Types de contraintes

| Type | Exemples |
|---|---|
| `health` | Blessure, maladie, douleur |
| `availability` | Vacances, déplacement pro |
| `schedule` | Événement ponctuel, réunion |
| `mental_state` | Surmenage, motivation basse |
| `preference` | Refus d'un type de séance |
| `equipment` | Accès piscine coupé, vélo en réparation |
