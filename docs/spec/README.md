# Specs — Garmin Coach Agent

## Brief

Garmin Coach Agent est un assistant local qui transforme des données Garmin en recommandations d’entraînement simples et actionnables.

Le but n’est pas d’exposer la base brute à l’agent, ni de multiplier les interfaces.
Le but est de garder une couche de données simple, locale et déterministe, puis de laisser l’agent raisonner sur des sorties structurées.

## Objectifs

Voir [`objectives.md`](objectives.md).

## Vue macro

La V0 repose sur cinq blocs :

- **Outils** : découpage fonctionnel des blocs métier et de leurs scripts
- **Scripts** : points d’entrée simples pour produire des snapshots
- **Cron** : exécutions planifiées pour garder les données fraîches
- **Base de données** : stockage local des activités et métriques utiles
- **Agent** : consommation des snapshots et génération de conseils

## Navigation

- [`objectives.md`](objectives.md)
- [`architecture.md`](architecture.md)
- [`code.md`](code.md)
- [`database.md`](database.md)
- [`scripts.md`](scripts.md)
- [`agent.md`](agent.md)
- [`export-workflow.md`](export-workflow.md) — validation locale et publication Garmin
- [`../../agent/README.md`](../../agent/README.md) — dossier de travail de l’agent
