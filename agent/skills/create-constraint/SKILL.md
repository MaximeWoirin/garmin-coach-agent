---
name: create-constraint
description: Use immediately when the user mentions an injury, availability issue, preference, or any constraint that should affect planning.
---

# create-constraint

## Quand l'utiliser

- Blessure, maladie, douleur
- Déplacement, vacances, indisponibilité
- Préférence forte ou contrainte matérielle
- Tout contexte qui doit devenir une entrée structurée en base

## Commande

```bash
<EXEC_DIR>/create-constraint \
  --type TYPE \
  --start-date YYYY-MM-DD \
  --raw-text "..." \
  [--goal-id N] \
  [--severity low|medium|high] \
  [--scope training|life|day|session] \
  [--end-date YYYY-MM-DD] \
  [--source SOURCE] \
  [--confidence FLOAT] \
  [--tags-json '["tag"]'] \
  [--notes-json '{"note":"..."}'] \
  [--status active|inactive] \
  [--dry-run]
```

## Points importants

- `--start-date` est requis.
- `--severity`, `--scope`, `--status` ont des valeurs par défaut valides.
- `--notes-json` et `--tags-json` doivent être du JSON sérialisé.

## Sortie typique

```json
{
  "status": "success",
  "constraint_id": 5,
  "constraint_status": "active"
}
```
