---
name: get-constraint-cleanup
description: Use to review active constraints and surface cleanup candidates before asking the user to archive anything.
---

# get-constraint-cleanup

## Quand l'utiliser

- Pour un récap hebdo de ménage des contraintes
- Avant de proposer de passer des contraintes en `inactive`
- Quand tu veux distinguer contraintes durables vs possiblement obsolètes

## Commande

```bash
<EXEC_DIR>/get-constraint-cleanup \
  [--scope training|life|day|session] \
  [--status active|inactive] \
  [--as-of YYYY-MM-DD] \
  [--stale-after-days N] \
  [--confidence-threshold 0.8] \
  [--limit N]
```

## Contrat réel

- S'appuie sur les contraintes existantes, sans rien muter.
- Enrichit chaque contrainte avec `cleanup_candidate` et `cleanup_reasons`.
- Retourne aussi `cleanup_candidates`, `summary` et `heuristics`.
- Les heuristiques restent prudentes : expirée, faible confiance, ou contrainte temporaire ancienne à reconfirmer.

## Sortie typique

```json
{
  "status": "success",
  "constraints": [
    {
      "id": 7,
      "type": "availability",
      "cleanup_candidate": true,
      "cleanup_reasons": [
        {
          "code": "stale_temporary",
          "label": "temporaire ancienne à reconfirmer",
          "details": "availability active depuis 35 jours sans end_date"
        }
      ]
    }
  ],
  "cleanup_candidates": [
    {
      "constraint_id": 7,
      "reasons": [
        {
          "code": "stale_temporary",
          "label": "temporaire ancienne à reconfirmer",
          "details": "availability active depuis 35 jours sans end_date"
        }
      ]
    }
  ],
  "summary": {
    "count": 1,
    "cleanup_candidate_count": 1,
    "cleanup_candidates_by_reason": {
      "stale_temporary": 1
    }
  },
  "heuristics": {
    "as_of": "2026-06-30",
    "stale_after_days": 21,
    "confidence_threshold": 0.8,
    "temporary_types": ["availability", "mental_state", "schedule"]
  }
}
```
