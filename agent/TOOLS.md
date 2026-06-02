# TOOLS

Cette page décrit quels scripts appeler selon l’intention.

Règle générale :
- d’abord lire
- ensuite décider
- écrire seulement si la mission demande une modification explicite

## Rafraîchir les données

### `sync-garmin`
À appeler quand :
- les données récentes sont absentes
- la dernière sync est ancienne
- on veut comparer plan prévu vs activités réelles

Ne pas appeler si :
- on sait déjà que l’auth Garmin n’est pas disponible
- la mission porte seulement sur une lecture historique locale

## Lire l’état sportif récent

### `get-fitness-state`
Pour obtenir :
- métriques journalières
- signal synthétique simple
- résumé de tendance

### `get-activities`
Pour obtenir :
- activités réellement effectuées
- volume récent
- type de séances faites

## Lire le contexte de planification

### `get-current-plan`
Pour obtenir :
- plan actif ou draft
- séances prévues
- statut du plan

### `get-constraints`
Pour obtenir :
- contraintes actives
- disponibilité
- préférences ou limites courantes

## Écrire / ajuster

### Plans
- `create-plan-draft`
- `create-plan-session`
- `delete-plan-session`
- `set-plan-status`
- `set-plan-session-status`

Outils à ajouter côté produit :
- `update-plan-session`
- `replace-plan-session`

### Contraintes
- `create-constraint`
- `delete-constraint`
- `set-constraint-status`

## Séquence recommandée par défaut

### Pour conseiller une séance du jour
1. `get-fitness-state`
2. `get-activities`
3. `get-current-plan`
4. `get-constraints`
5. réponse coach

### Pour revoir un plan de semaine
1. `sync-garmin` si nécessaire
2. `get-fitness-state`
3. `get-activities`
4. `get-current-plan`
5. `get-constraints`
6. proposition d’ajustement

## Workflow de validation / export

- le plan peut être validé localement avant publication Garmin
- les séances `proposed` sont considérées prêtes mais pas forcément publiées
- l’export Garmin doit idéalement ne publier que l’horizon court
- une séance `proposed` est éditable
- une séance `exported` doit être remplacée proprement, pas mutée librement

## Règles de prudence

- ne pas modifier un plan sans demande explicite
- ne pas archiver / envoyer un plan automatiquement
- ne pas supposer qu’une séance prévue a été faite sans réconciliation explicite
