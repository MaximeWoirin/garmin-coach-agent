---
name: delete-constraint
description: Use to delete a constraint that was created by mistake.
---

# delete-constraint

## Quand l'utiliser

- Doublon manifeste
- Mauvaise contrainte créée par erreur
- Nettoyage d'une donnée invalide avant usage

## Commande

```bash
python -m garmin_coach.delete_constraint \
  --constraint-id N \
  [--dry-run]
```

## Contrat réel

- Le script supprime la ligne si elle existe.
- En `--dry-run`, il ne supprime rien et renvoie `constraint_id` + `dry_run`.
- Si tu veux conserver l'historique plutôt que supprimer, préférer `set-constraint-status --status inactive`.

## Sortie typique

```json
{
  "status": "success",
  "constraint_id": 5
}
```
