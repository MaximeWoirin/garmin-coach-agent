# Architecture macro

## Principe

L’architecture reste volontairement petite.
On préfère quelques briques stables plutôt qu’un système trop large dès le départ.

## Blocs

### 1. Mémoire agent

La mémoire longue durée garde le contexte stable : objectifs, préférences, contraintes persistantes, leçons apprises.
Elle ne remplace pas la base, mais elle complète les données structurées.

### 2. Scripts

Des commandes CLI produisent des snapshots JSON simples et lisibles.
Elles servent de contrat entre les données et l’agent.

### 3. Cron

Un cron lance les jobs récurrents.
En V0, il sert surtout à déclencher `sync-garmin` tous les jours tôt le matin, autour de 4h UTC, pour importer les activités de la veille et les daily metrics, avec un petit lookback si nécessaire.
Son rôle est opérationnel, pas “intelligent”.

### 4. Base de données

SQLite stocke les activités, les métriques journalières, les contraintes actives, les plans générés et l’historique des synchronisations.
Elle sert de source locale de vérité pour le plan vivant.

### 5. Agent

L’agent ne lit pas la base directement.
Il combine la mémoire stable et les snapshots produits par les scripts pour formuler une recommandation courte.

## Flux attendu

```text
Garmin source -> sync -> SQLite -> scripts -> JSON snapshot -> agent -> conseil
```

## Ce qu’on évite en V0

- interface web
- logique métier dispersée dans plusieurs endroits
- SQL libre exposé à l’agent
- orchestration complexe
