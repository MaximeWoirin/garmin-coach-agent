---
name: get-constraints
description: Use to read stored constraints before planning or adaptation.
---

# get-constraints

## Quand l'utiliser

- Avant la planification
- Avant d'adapter une semaine
- Pour voir les contraintes encore actives

## Commande

```bash
<EXEC_DIR>/get-constraints \
  [--scope training|life|day|session] \
  [--status active|inactive] \
  [--limit N]
```

## Contrat réel

- Le filtre réel est `--scope`, pas `--plan-id` / `--session-id`.
- `--status` vaut `active` par défaut.
- La sortie contient `constraints` et `summary`.

## Sortie typique

```json
{
  "status": "success",
  "constraints": [],
  "summary": {
    "count": 0,
    "by_type": {},
    "by_severity": {}
  }
}
```
