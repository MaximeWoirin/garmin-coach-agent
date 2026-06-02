# Scripts

## Rôle

Les scripts sont les points d’entrée stables du projet.
Ils lisent la base, calculent le minimum utile, puis sortent du JSON.

Cette page inventorie les scripts par état actuel.
Le découpage fonctionnel détaillé vit dans [`tools.md`](tools.md).

## Implémentation Garmin

Pour toutes les intégrations Garmin, le projet doit utiliser **`python-garminconnect`**.
On n’utilise pas `garth` directement.

## Vue rapide

La cartographie métier vit dans [`tools.md`](tools.md).
Cette page reste l’inventaire des scripts et de leur contrat d’entrée/sortie.

## Scripts prévus

### auth-garmin

```bash
python -m garmin_coach.auth_garmin
```

Script d’authentification Garmin pour le premier setup et les ré-authentifications.

Entrées :
- `--tokens-dir` : répertoire de stockage des tokens, optionnel
- `--email` : email Garmin, optionnel si saisi interactif
- `--password` : mot de passe Garmin, optionnel si saisi interactif
- `--force-login` : force un login complet même si des tokens existent

Sortie :
- JSON avec le statut d’authentification et le chemin du store de tokens

Comportement backbone :
- utilise `python-garminconnect`
- réalise le login interactif
- gère le MFA si nécessaire
- enregistre les tokens localement
- sert au premier setup et au recovery si le refresh token n’est plus valable

Interface JSON minimale :
- `status` : `success | failed`
- `tokens_path`
- `warnings[]`
- `errors[]`

### create-plan-draft

```bash
python -m garmin_coach.create_plan_draft --week-start 2026-06-01 --week-end 2026-06-08
```

Script de création d’un plan local en draft.

Entrées :
- `--week-start` : date ISO `YYYY-MM-DD`, début de semaine, obligatoire
- `--week-end` : date ISO `YYYY-MM-DD`, fin de semaine, obligatoire
- `--goal-id` : identifiant d’objectif, optionnel
- `--block-id` : identifiant de bloc macro, optionnel
- `--title` : titre libre du plan, optionnel
- `--notes` : notes initiales, optionnel
- `--metadata-json` : métadonnées supplémentaires, optionnel
- `--sessions-json` : définition initiale des séances du plan, optionnel
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec le plan créé, ses métadonnées, les séances créées et les avertissements éventuels

Comportement backbone :
- crée `training_plans`
- crée les `plan_sessions` associées
- garde le plan en statut draft
- valide les champs canonique / dates / cohérence
- reste idempotent si on lui donne un identifiant de reprise

Interface JSON minimale :
- `status` : `success | partial | failed`
- `plan_id`
- `week_start`, `week_end`
- `plan_status`
- `sessions_created`
- `warnings[]`, `errors[]`

### create-plan-session

```bash
python -m garmin_coach.create_plan_session --plan-id 42 --planned-date 2026-06-03 --activity-type run --duration-min 45
```

Script de création d’une séance dans un plan, par défaut en état draft.

Entrées :
- `--plan-id` : identifiant du plan parent, obligatoire
- `--planned-date` : date ISO `YYYY-MM-DD`, obligatoire
- `--planned-time` : heure locale optionnelle
- `--activity-type` : type d’activité, obligatoire
- `--duration-min` : durée cible en minutes, obligatoire
- `--intensity` : intensité cible, optionnelle
- `--target-hr-low` : borne basse FC, optionnelle
- `--target-hr-high` : borne haute FC, optionnelle
- `--target-pace-sec-per-km` : allure cible, optionnelle
- `--target-rpe` : RPE cible, optionnelle
- `--status` : statut initial, défaut `draft`
- `--tags-json` : tags supplémentaires, optionnel
- `--notes` : notes, optionnel
- `--workout-payload-json` : payload exportable Garmin, optionnel
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec la séance créée, son statut, et les validations éventuelles

Comportement backbone :
- crée une `plan_session`
- rattache la séance au plan demandé
- garde la séance en état éditable par défaut
- valide la cohérence des cibles et des dates
- reste idempotent si on lui donne une clé de reprise

Interface JSON minimale :
- `status` : `success | partial | failed`
- `plan_id`
- `session_id`
- `session_status`
- `warnings[]`, `errors[]`

### delete-plan-session

```bash
python -m garmin_coach.delete_plan_session --plan-id 42 --session-id 7
```

Script de suppression d’une séance de plan.

Entrées :
- `--plan-id` : identifiant du plan, obligatoire
- `--session-id` : identifiant de la séance, obligatoire
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec la séance supprimée et les éventuels avertissements

Comportement backbone :
- supprime une `plan_session` seulement si elle est encore éditable
- refuse la suppression si la séance est déjà exportée ou réalisée
- reste strict pour préserver la réconciliation

Interface JSON minimale :
- `status` : `success | partial | failed`
- `plan_id`
- `session_id`
- `warnings[]`
- `errors[]`

## Workflow recommandé

Le workflow cible est :
- validation locale du plan et des séances
- publication Garmin séparée
- export progressif sur horizon court plutôt qu’export complet immédiat

Conséquence :
- `set-plan-status` sert à valider localement
- `export-plan-garmin` sert à publier
- `sync-garmin` sert à réconcilier le réalisé

### set-plan-status

```bash
python -m garmin_coach.set_plan_status --plan-id 42 --status active
```

Script de changement du statut d’un plan.

Entrées :
- `--plan-id` : identifiant du plan, obligatoire
- `--status` : nouveau statut du plan, obligatoire
- `--cascade-sessions` : applique aussi une transition de statut aux séances si pertinent
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec le plan mis à jour, les transitions de séances et les validations éventuelles

Comportement backbone :
- change le statut du plan
- sert d’abord à la validation locale
- peut faire passer les séances de `draft` à `proposed` quand le plan est validé
- ne doit pas impliquer automatiquement un export complet vers Garmin
- conserve la cohérence du workflow sans casser l’historique

Interface JSON minimale :
- `status` : `success | partial | failed`
- `plan_id`
- `plan_status`
- `session_status_changes[]`
- `warnings[]`
- `errors[]`

### set-plan-session-status

```bash
python -m garmin_coach.set_plan_session_status --plan-id 42 --session-id 7 --status exported
```

Script de changement granulaire du statut d’une séance de plan.

Entrées :
- `--plan-id` : identifiant du plan, obligatoire
- `--session-id` : identifiant de la séance, obligatoire
- `--status` : nouveau statut de séance, obligatoire
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec la séance mise à jour et les validations éventuelles

Comportement backbone :
- modifie uniquement le statut de la séance
- ne touche pas au contenu de la séance
- reste utile pour export, done, skipped, canceled et réconciliation

Interface JSON minimale :
- `status` : `success | partial | failed`
- `plan_id`
- `session_id`
- `session_status`
- `warnings[]`
- `errors[]`

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
- JSON de sync avec statut, compteurs, plage lue, réconciliation éventuelle, erreurs éventuelles

Comportement backbone :
- importe les activités Garmin
- importe les daily metrics Garmin
- met à jour `sync_runs`
- réconcilie le plan local avec le réel importé
- met à jour les matches et statuts de séances si nécessaire
- reste idempotent

Interface JSON minimale :
- `status` : `success | partial | failed`
- `source` : `garmin`
- `range_start`, `range_end`
- `activities_seen`, `activities_inserted`, `activities_updated`
- `daily_metrics_seen`, `daily_metrics_upserted`
- `reconciled_sessions`, `matched_activities`
- `warnings[]`, `errors[]`

### get-current-plan

```bash
python -m garmin_coach.get_current_plan
```

Script de lecture du plan courant.

Entrées :
- `--plan-id` : plan précis, optionnel
- `--week-start` : plan de la semaine, optionnel
- `--include-sessions` : inclut les séances détaillées
- `--include-metadata` : inclut les métadonnées du plan

Sortie :
- JSON avec le plan courant, son statut, ses séances et ses métadonnées utiles

Contenu attendu :
- plan actif ou draft
- séances associées
- résumé compact pour l’agent

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

### get-goals

```bash
python -m garmin_coach.get_goals --status active
```

Tool de lecture pour récupérer les objectifs d’entraînement utiles à l’agent.

Entrées :
- `--status` : filtre optionnel, par défaut les objectifs actifs
- `--limit` : optionnel, nombre max d’objectifs
- `--include-archived` : optionnel, inclut les objectifs archivés

Sortie :
- JSON avec la liste des objectifs et un résumé compact

Contenu attendu :
- objectifs longs termes et leur contexte
- priorité canonique
- état courant du cycle de vie de l’objectif
- éventuels champs `raw_text` si l’entrée humaine est plus nuancée que la valeur normalisée

### export-plan-garmin

```bash
python -m garmin_coach.export_plan_garmin --plan-id 42
```

Script d’export d’un plan local vers Garmin.

Entrées :
- `--plan-id` : identifiant du plan à exporter, obligatoire dans le cas simple
- `--week-start` : alternative si on veut cibler le plan actif d’une semaine
- `--dry-run` : simule l’export sans écrire côté Garmin ni en base
- `--force` : réécrit l’export même si des séances ont déjà un `garmin_event_id`

Sortie :
- JSON avec le plan exporté, le nombre de séances traitées, les ids Garmin créés / mis à jour, les conflits éventuels

Comportement backbone :
- lit `training_plans` et `plan_sessions`
- cible en priorité les séances `proposed`
- pousse les séances à Garmin
- stocke `garmin_event_id`
- passe les séances exportées au statut `exported`
- doit évoluer vers un export filtré par horizon court / plage de dates
- reste idempotent autant que possible
- remonte clairement les erreurs de mapping ou de validation

Interface JSON minimale :
- `status` : `success | partial | failed`
- `plan_id`
- `week_start`, `week_end`
- `sessions_seen`, `sessions_exported`, `sessions_skipped`, `sessions_failed`
- `garmin_event_ids[]`
- `warnings[]`, `errors[]`

Contenu attendu :
- plan exporté
- séances exportées, ignorées ou en erreur
- statut final de l’export
- éventuels avertissements de conflit

### create-constraint

```bash
python -m garmin_coach.create_constraint --type availability --scope training --start-date 2026-06-01 --raw-text "Pas dispo mardi soir"
```

Script de création d’une contrainte.

Entrées :
- `--goal-id` : identifiant d’objectif lié, optionnel
- `--type` : type de contrainte, obligatoire
- `--severity` : sévérité canonique, optionnelle, défaut `medium`
- `--scope` : périmètre canonique, optionnel, défaut `training`
- `--start-date` : date ISO `YYYY-MM-DD`, obligatoire
- `--end-date` : date ISO `YYYY-MM-DD`, optionnelle
- `--source` : origine, optionnelle, défaut `user`
- `--confidence` : niveau de confiance, optionnel
- `--raw-text` : formulation brute, obligatoire
- `--tags-json` : tags supplémentaires, optionnel
- `--notes-json` : notes structurées, optionnel
- `--status` : statut initial, défaut `active`
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec la contrainte créée et les validations éventuelles

Interface JSON minimale :
- `status` : `success | partial | failed`
- `constraint_id`
- `constraint_status`
- `warnings[]`
- `errors[]`

### delete-constraint

```bash
python -m garmin_coach.delete_constraint --constraint-id 12
```

Script de suppression d’une contrainte.

Entrées :
- `--constraint-id` : identifiant de contrainte, obligatoire
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec la contrainte supprimée et les validations éventuelles

Interface JSON minimale :
- `status` : `success | partial | failed`
- `constraint_id`
- `warnings[]`
- `errors[]`

### set-constraint-status

```bash
python -m garmin_coach.set_constraint_status --constraint-id 12 --status inactive
```

Script de changement de statut d’une contrainte.

Entrées :
- `--constraint-id` : identifiant de contrainte, obligatoire
- `--status` : nouveau statut, obligatoire
- `--dry-run` : simule sans écrire

Sortie :
- JSON avec la contrainte mise à jour et les validations éventuelles

Interface JSON minimale :
- `status` : `success | partial | failed`
- `constraint_id`
- `constraint_status`
- `warnings[]`
- `errors[]`

### get-constraints

```bash
python -m garmin_coach.get_constraints --scope training --status active
```

Tool de lecture pour récupérer les contraintes utiles à l’agent.

Entrées :
- `--scope` : filtre optionnel sur le périmètre
- `--status` : filtre optionnel, par défaut les contraintes actives
- `--limit` : optionnel, nombre max de contraintes

Sortie :
- JSON avec la liste des contraintes et un résumé compact

Contenu attendu :
- contraintes de routine, de santé, de dispo, de préférence ou d’équipement
- statut canonique
- sévérité canonique
- `raw_text` quand il faut conserver la formulation d’origine

## Contrat

- sortie JSON
- erreurs explicites si donnée manquante
- pas de logique cachée dans le prompt
- pas de SQL libre côté agent
- les scripts de backbone doivent être idempotents
- les scripts d’écriture doivent journaliser les conflits et les rejets

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
- `constraint.status` → `active | inactive`
- `constraint.scope` → `training | life | day | session`
- `constraint.severity` → `low | medium | high`
- `training_block.block_type` → `build | recover | peak | taper`
- `training_plans.status` → `draft | active | sent | archived`
- `plan_session.status` → `draft | proposed | exported | done | skipped | canceled`
- `plan_review.outcome` → `kept | adapted | reset`
- `plan_activity_matches.match_type` → `manual | inferred | imported`
- `activity.source` → `garmin | manual`

## Convention

Ces scripts doivent rester fins.
La logique métier importante vit dans le code Python réutilisable.
