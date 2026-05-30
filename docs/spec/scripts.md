# Scripts

## Rôle

Les scripts sont les points d’entrée stables du projet.
Ils lisent la base, calculent le minimum utile, puis sortent du JSON.

## Scripts prévus

### sync-garmin

```bash
python -m garmin_coach.sync_garmin
```

Script d’ingestion quotidien.

Il est appelé par le cron, idéalement tôt le matin vers 4h UTC, et doit récupérer l’état utile de la veille, puis mettre à jour la base.

Contenu attendu :
- activités de la veille
- daily metrics de la veille
- éventuellement un petit lookback sur quelques jours pour rattraper les données Garmin arrivées en retard

Rôle :
- alimenter SQLite
- mettre à jour l’historique de sync
- garder les snapshots à jour
- rester idempotent

Entrées :
- aucune entrée manuelle obligatoire
- paramètres optionnels de source / plage si on veut rejouer un import

Sortie :
- JSON de sync avec statut, compteurs, plage lue, erreurs éventuelles

### get-activities

```bash
python -m garmin_coach.get_activities --start 2026-05-01 --end 2026-05-15
```

Tool de lecture générique pour les activités sur une période.

Entrées :
- `--start` : date ISO `YYYY-MM-DD` incluse
- `--end` : date ISO `YYYY-MM-DD` exclue
- `--limit` : optionnel, nombre max de lignes
- `--activity-type` : optionnel, filtre par type

Sortie :
- JSON avec la période demandée, la liste des activités et un petit résumé agrégé

Contenu attendu :
- activités sur la plage demandée
- résumé de volume
- résumé d’intensité si disponible

### get-fitness-state

```bash
python -m garmin_coach.get_fitness_state --start 2026-05-01 --end 2026-05-15
```

Tool de lecture générique pour l’état de forme sur une période.

Entrées :
- `--start` : date ISO `YYYY-MM-DD` incluse
- `--end` : date ISO `YYYY-MM-DD` exclue
- `--limit` : optionnel, nombre max de jours

Sortie :
- JSON avec la période demandée, les daily metrics et un résumé d’état de forme

Contenu attendu :
- daily metrics sur la plage demandée
- tendances simples : stress, resting HR, Body Battery, intensité
- signal synthétique lisible par l’agent

## Contrat

- sortie JSON
- erreurs explicites si donnée manquante
- pas de logique cachée dans le prompt
- pas de SQL libre côté agent

## Enums et validation

Les scripts d’écriture doivent utiliser des valeurs canoniques pour éviter les ambiguïtés.

### Règle

- l’input peut accepter quelques alias utiles
- le script normalise vers une valeur canonique
- si la valeur n’est pas reconnue, le script renvoie une erreur claire
- `raw_text` conserve la nuance humaine quand nécessaire

### Enums canoniques à cadrer

- `goal.priority` → `low | medium | high`
- `constraint.type` → `availability | health | mental_state | preference | schedule | equipment`
- `constraint.status` → `active | resolved | archived`
- `constraint.scope` → `training | life | day | session`
- `constraint.severity` → `low | medium | high`
- `training_block.block_type` → `build | recover | peak | taper`
- `training_plan.status` → `draft | active | sent | archived`
- `plan_session.status` → `proposed | exported | done | skipped | canceled`
- `plan_review.outcome` → `kept | adapted | reset`
- `plan_activity_matches.match_type` → `manual | inferred | imported`

## Convention

Ces scripts doivent rester fins.
La logique métier importante vit dans le code Python réutilisable.
