---
name: set-constraint-status
description: Use to switch a stored constraint between active and inactive.
---

# set-constraint-status

## Quand l'utiliser

- Une contrainte ne s'applique plus
- Une contrainte redevient active
- Il faut conserver l'historique sans supprimer la ligne

## Commande

```bash
<EXEC_DIR>/set-constraint-status \
  --constraint-id N \
  --status active|inactive \
  [--dry-run]
```

## Contrat réel

- Les seuls statuts gérés par l'implémentation actuelle sont `active` et `inactive`.
- `inactive` renseigne `resolved_at` côté base.
- La sortie renvoie `constraint_status`, pas `old_status` / `new_status`.

## Sortie typique

```json
{
  "status": "success",
  "constraint_id": 5,
  "constraint_status": "inactive"
}
```
