---
name: get-current-plan
description: Use to read the current plan, or a targeted plan by id or week.
---

# get-current-plan

## Quand l'utiliser

- Voir le plan courant
- Contrôler une semaine avant adaptation
- Vérifier les statuts de séances avant export

## Commande

```bash
python -m garmin_coach.get_current_plan \
  [--plan-id N] \
  [--week-start YYYY-MM-DD] \
  [--include-sessions] \
  [--include-metadata]
```

## Contrat réel

- Les vrais flags sont `--plan-id`, `--week-start`, `--include-sessions`, `--include-metadata`.
- Il n'existe pas de `--session-id`.
- En pratique, les séances sont déjà incluses par défaut par le script actuel.
- La sortie contient `plan_status` et, si activé, `sessions` + `sessions_count`.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "week_start": "2026-06-16",
  "week_end": "2026-06-22",
  "plan_status": "active",
  "needs_review": false,
  "sessions": [],
  "sessions_count": 0
}
```
