---
name: export-plan-garmin
description: Use to push the validated training plan to Garmin Connect so sessions appear in the user's Garmin device.
---

# export-plan-garmin

## Quand l'utiliser

- Après avoir validé le plan (`set-plan-status --status active`)
- Quand l'utilisateur dit "envoie le plan sur ma montre" ou "je veux voir mes séances sur Garmin"
- Toujours en fin de cycle de construction : create-plan-draft → create-plan-session × N → set-plan-status active → **export**

## Prérequis

1. Le plan doit être en statut `active`
2. `auth-garmin` doit être valide (token actif)
3. Les séances doivent avoir des dates et durées renseignées

## Commande

```bash
python -m garmin_coach.export_plan_garmin \
  --plan-id N \
  [--session-id N] \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--plan-id` | Oui | ID du plan à exporter |
| `--session-id` | Non | Exporter une seule séance (partiel) |
| `--dry-run` | Non | Simule sans appeler l'API Garmin |

## Sortie

```json
{
  "status": "success",
  "plan_id": 42,
  "exported_sessions": [7, 8, 9],
  "garmin_workout_ids": ["abc123", "def456", "ghi789"],
  "warnings": []
}
```

## Après l'export

- Appeler `set-plan-status --status exported` pour mettre à jour le statut
- Les séances exportées passent automatiquement en statut `exported`
- En cas d'échec partiel, les `warnings[]` listent les séances non exportées
