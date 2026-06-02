---
name: delete-constraint
description: Use to permanently remove a constraint that was entered by mistake or that no longer applies.
---

# delete-constraint

## Quand l'utiliser

- Une contrainte a été créée par erreur (doublon, mauvaise info)
- La contrainte n'a jamais été valide et n'a affecté aucun plan

## Ne pas utiliser

- Si la contrainte s'est résolue naturellement → utiliser `set-constraint-status --status resolved`
- Si la contrainte est liée à des plans existants (le script peut refuser)

## Commande

```bash
python -m garmin_coach.delete_constraint \
  --constraint-id N \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--constraint-id` | Oui | ID de la contrainte à supprimer |
| `--dry-run` | Non | Simule sans supprimer |

## Sortie

```json
{
  "status": "success",
  "constraint_id": 5,
  "warnings": []
}
```

## Précaution

Préférer `set-constraint-status --status resolved` dans la majorité des cas.  
La suppression efface l'historique ; la résolution le conserve.
