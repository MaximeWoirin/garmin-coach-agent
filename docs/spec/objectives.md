# Objectifs

## Objectif principal

Le projet sert à construire un coach Garmin personnel qui :

- planifie une semaine d’entraînement cohérente avec les objectifs à moyen terme
- tient compte des séances passées, du cycle de travail en cours et des séances à venir
- adapte le plan au jour le jour selon la fatigue, le stress et le temps disponible
- permet une discussion naturelle avec l’agent pour ajuster le plan si besoin

## Usage cible

Le système est strictement personnel.
Il n’est pas pensé comme un produit multi-utilisateur ni comme une plateforme générale.

## Résultats attendus

Le projet doit produire :

- un récapitulatif hebdomadaire de la semaine passée et de la semaine à venir
- des séances planifiées dans l’app Garmin
- des échanges avec l’agent pour adapter l’entraînement au quotidien

## Niveau de V0

La V0 doit rester simple sur les indicateurs analysés.
En revanche, les boucles hebdomadaires et la synchronisation Garmin doivent être fiables.

## Données nécessaires

Le minimum utile pour faire un plan comprend :

- les activités passées
- les activités planifiées
- des indicateurs physiologiques globaux pour suivre la forme
- des métadonnées sur le plan d’entraînement
- les objectifs
- les contraintes personnelles et de routine

## Exclusions explicites

On exclut pour l’instant :

- sommeil
- GPS
- UI web
- multi-user

## Critère de succès

Le projet est réussi si :

- le plan est cohérent
- il s’adapte bien à la routine
- il reste raisonnable face au niveau d’ambition réel
- il peut pousser l’agent à proposer une révision des objectifs quand le niveau d’ambition semble trop haut ou trop bas

## Sorties de l’outil

Les sorties attendues côté utilisateur sont :

- des conversations avec l’agent
- des activités / séances Garmin
