---
name: create-constraint
description: Use immediately when the user mentions any limitation — injury, travel, fatigue, schedule conflict — that affects their training.
---

# create-constraint

## Quand l'utiliser

- L'utilisateur mentionne une blessure, douleur, ou contre-indication médicale
- L'utilisateur annonce des vacances, déplacements, ou indisponibilités
- L'utilisateur exprime une préférence forte (ex: "pas de séances le mercredi")
- L'utilisateur signale un état mental ou fatigue inhabituelle
- **Capturer immédiatement** : ne pas attendre la prochaine session de planification

## Commande

```bash
python -m garmin_coach.create_constraint \
  --type TYPE \
  --severity SEVERITY \
  --raw-text "..." \
  [--scope SCOPE] \
  [--start-date YYYY-MM-DD] \
  [--end-date YYYY-MM-DD] \
  [--tags-json '["tag1","tag2"]'] \
  [--dry-run]
```

## Paramètres clés

| Paramètre | Requis | Description |
|---|---|---|
| `--type` | Oui | Catégorie (voir tableau ci-dessous) |
| `--severity` | Oui | `low` / `medium` / `high` |
| `--raw-text` | Oui | Description libre en langage naturel |
| `--scope` | Non | `training` / `life` / `day` / `session` |
| `--start-date` | Non | Début (défaut : aujourd'hui) |
| `--end-date` | Non | Fin (vide = indéfinie) |

## Types de contraintes

| Type | Exemples |
|---|---|
| `health` | Genou douloureux, rhume, fatigue musculaire |
| `availability` | Vacances, déplacement, week-end chargé |
| `schedule` | Réunion le soir, enfant malade |
| `mental_state` | Surmenage, démotivation, stress élevé |
| `preference` | Refuse la natation, préfère ne pas courir le lundi |
| `equipment` | Vélo en réparation, piscine fermée |

## Sortie

```json
{
  "status": "success",
  "constraint_id": 5,
  "type": "health",
  "severity": "medium",
  "status": "active"
}
```

## Exemple typique

```bash
python -m garmin_coach.create_constraint \
  --type health \
  --severity medium \
  --raw-text "Douleur genou gauche depuis lundi, pas de course pendant 2 semaines" \
  --start-date 2025-01-13 \
  --end-date 2025-01-26 \
  --tags-json '["knee","no-running"]'
```
