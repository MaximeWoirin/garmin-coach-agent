---
name: create-plan-session
description: Use after create-plan-draft to add one session to a plan.
---

# create-plan-session

## Quand l'utiliser

- Ajouter une séance à un plan existant
- Compléter un draft semaine par semaine
- Remplacer une séance non exportée via delete + create

## Commande

```bash
<EXEC_DIR>/create-plan-session \
  --plan-id N \
  --planned-date YYYY-MM-DD \
  --activity-type TYPE \
  --duration-min N \
  [--planned-time HH:MM] \
  [--intensity TEXT] \
  [--target-hr-low N] \
  [--target-hr-high N] \
  [--target-pace-sec-per-km N] \
  [--target-rpe N] \
  [--status draft|proposed|exported|done|skipped|canceled] \
  [--tags-json '["tag"]'] \
  [--notes "..."] \
  [--session-payload-json '{...}'] \
  [--session-payload-file /path/to/session.json] \
  [--workout-payload-json '{"workoutName":"..."}'] \
  [--dry-run]
```

## Points importants

- `--plan-id`, `--planned-date`, `--activity-type`, `--duration-min` sont requis.
- `--status` existe vraiment et vaut `draft` par défaut.
- `--session-payload-json` et `--session-payload-file` sont les entrées à privilégier pour une séance running structurée V1.
- `--session-payload-json` et `--session-payload-file` sont mutuellement exclusifs.
- `--workout-payload-json` reste un escape hatch technique quand un payload Garmin précis est déjà préparé.

## Quand utiliser une séance structurée

Utiliser `session_payload_json` pour les vraies séances Garmin de course quand le rendu des étapes compte vraiment :

- `running`
- `trail`
- `treadmill`

Typiquement : fractionné, tempo structuré, séance avec répétitions, échauffement / récupération distincts.

Rester en mode simple quand la séance est juste :

- une durée
- une intensité éventuelle
- une note lisible

## Bonne structure V1

Pour une bonne séance structurée V1 :

- `format = "structured"`
- `sport` dans `running|trail|treadmill`
- suite ordonnée de `items`
- `kind = "step"` ou `kind = "repeat"`
- `warmup` / bloc principal / `cooldown` recommandés, mais pas imposés
- end conditions V1 : `time`, `distance`, `lap_button`
- targets V1 : `pace`, `heart_rate_zone`

Préférer une structure simple et Garmin-like :

- pas de blocs abstraits inutiles
- pas de JSON verbeux si une séance simple suffit
- commentaires utiles au niveau des `step`, pas roman global dans `notes`

## Sortie typique

```json
{
  "status": "success",
  "plan_id": 42,
  "session_id": 7,
  "session_status": "draft"
}
```
