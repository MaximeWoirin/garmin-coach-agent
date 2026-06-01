# Métriques physiologiques

## Rôle

Fournir les données physiologiques journalières utiles au raisonnement d’entraînement.

## Existant

- `sync-garmin`
- `get-fitness-state`

## Couverture actuelle

- synchro Garmin ✅
- lecture / snapshot ✅

## Ce qui manque

- rien de bloquant pour la V0
- éventuellement des vues spécialisées plus tard si le besoin apparaît

## Dépendances

- table `daily_metrics`
- import Garmin
- calculs simples de tendance / résumé

## Questions ouvertes

- doit-on ajouter des vues plus ciblées, ou garder un seul snapshot générique ?
- quelles tendances doivent être exposées au coach sans gonfler le contrat ?
