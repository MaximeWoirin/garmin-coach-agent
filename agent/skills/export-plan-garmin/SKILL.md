---
name: export-plan-garmin
description: Use to export plan sessions to Garmin Connect on a short horizon.
---

# export-plan-garmin

## Quand l'utiliser

- Après validation locale d'un plan (`draft -> active`)
- Pour pousser seulement l'horizon court vers Garmin
- Quand l'utilisateur veut voir les prochaines séances sur Garmin

## Règles de workflow

- L'export est piloté au niveau **session**.
- Par défaut, seules les séances `proposed` sont exportables.
- Les séances `draft` ne partent pas.
- Les séances `exported` ne repartent pas, sauf `--force`.
- `set-plan-status` ne publie pas sur Garmin ; il valide seulement le cycle local du plan.
- **Ne jamais appeler `export-plan-garmin` sans borne d'horizon par défaut.**
- Sauf demande explicite de l'utilisateur pour publier tout un plan, toujours fournir `--days-ahead` ou `--start-date` / `--end-date`.
- Le cas normal est un export horizon court : demain, ou les prochains jours seulement.

## Règles de mapping sport Garmin

- Pour un **workout Garmin**, utiliser uniquement le mapping validé dans `docs/spec/garmin-workout-sport-mapping.md`.
- Ne jamais réutiliser directement les ids de `activity-service/activityTypes` pour remplir `sportTypeId`.
- Ne pas déduire un `sportTypeId` Garmin « plausible » depuis un nom de sport non documenté.
- Si le sport local n'a pas de type workout Garmin validé, utiliser seulement le fallback produit documenté.
- Fallbacks actuellement validés dans ce repo :
  - `hiking` -> `walking`
  - `climbing` / `rock_climbing` / `indoor_climbing` -> `other`
- Exemples sûrs :
  - `strength` -> `5 / strength_training`
  - `walking` -> `12 / walking`
  - `rucking` -> `13 / rucking`

## Commande

```bash
<EXEC_DIR>/export-plan-garmin \
  (--plan-id N | --week-start YYYY-MM-DD) \
  [--start-date YYYY-MM-DD] \
  [--end-date YYYY-MM-DD] \
  [--days-ahead N] \
  [--dry-run] \
  [--force]
```

## Contrat réel

- Il faut fournir `--plan-id` **ou** `--week-start`.
- `--start-date`, `--end-date`, `--days-ahead` bornent l'horizon d'export.
- Sans borne, le script peut exporter toutes les séances `proposed` du plan : considérer cela comme un mode exceptionnel.
- `--force` permet une réexport explicite des séances déjà `exported`.
- La sortie contient `sessions_seen`, `sessions_exported`, `sessions_skipped`, `sessions_ignored`, `sessions_failed`, `garmin_event_ids`.

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "week_start": "2026-06-16",
  "week_end": "2026-06-22",
  "sessions_seen": 5,
  "sessions_exported": 2,
  "sessions_skipped": 2,
  "sessions_ignored": 1,
  "sessions_failed": 0,
  "garmin_event_ids": ["dry-run-7", "dry-run-8"]
}
```
