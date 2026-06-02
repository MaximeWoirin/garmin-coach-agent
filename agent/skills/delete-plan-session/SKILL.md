---
name: delete-plan-session
description: Use to permanently remove a session from a plan when it was added by mistake or needs to be replaced.
---

# delete-plan-session

## Quand l'utiliser

- Une séance a été créée par erreur (mauvais jour, doublon)
- L'utilisateur demande à modifier une séance (supprimer + recréer)
- Restructuration du plan avant activation

## Ne pas utiliser

- Pour marquer une séance annulée → utiliser `set-plan-session-status --status skipped`
- Si la séance est déjà `exported` ou `done` (le script refusera)

## Commande

```bash
python -m garmin_coach.delete_plan_session \
  --plan-id N \
  --session-id N \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--plan-id` | Oui | ID du plan parent |
| `--session-id` | Oui | ID de la séance à supprimer |
| `--dry-run` | Non | Simule sans supprimer |

## Sortie

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7,
  "warnings": []
}
```

## Précaution

Toujours utiliser `--dry-run` d'abord pour confirmer que c'est la bonne séance.  
La suppression est irréversible.
