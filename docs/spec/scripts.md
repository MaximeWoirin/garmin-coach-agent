# Scripts

## Rôle

Les scripts sont les points d’entrée stables du projet.
Ils lisent la base, calculent le minimum utile, puis sortent du JSON.

## Scripts prévus

### sync-garmin

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

### coach-today

Produit un snapshot du jour.

Contenu attendu :
- activités récentes
- métriques journalières utiles
- signal de fatigue / fraîcheur
- recommandation courte

### coach-week

Produit une vue plus large sur la semaine.

Contenu attendu :
- charge récente
- tendance de volume
- séquence de séances dures
- vue synthétique de la récupération

## Contrat

- sortie JSON
- erreurs explicites si donnée manquante
- pas de logique cachée dans le prompt
- pas de SQL libre côté agent

## Convention

Ces scripts doivent rester fins.
La logique métier importante vit dans le code Python réutilisable.
