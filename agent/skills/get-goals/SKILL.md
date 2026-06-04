---
name: get-goals
description: Use to read training goals stored in the local database.
---

# get-goals

## Quand l'utiliser

- Avant de créer un plan
- Quand l'utilisateur demande ses objectifs actifs
- Pour vérifier priorité et horizon des objectifs

## Commande

```bash
<EXEC_DIR>/get-goals \
  [--status active|archived|completed|canceled] \
  [--limit N] \
  [--include-archived]
```

## Contrat réel

- Les vrais flags sont `--status`, `--limit`, `--include-archived`.
- Il n'existe pas de `--plan-id` ni `--goal-id`.
- La sortie contient `goals` et `summary`.

## Sortie typique

```json
{
  "status": "success",
  "goals": [],
  "summary": {
    "count": 0,
    "by_priority": {}
  }
}
```
