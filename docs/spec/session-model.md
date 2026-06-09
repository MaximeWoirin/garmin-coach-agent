# Modèle de séance

## Principe

On garde un **modèle commun partagé** pour toutes les activités.

Règle simple :
- **toutes les activités ont une durée obligatoire**
- certaines activités seulement ont une structure enrichie
- le reste retombe sur une version simple, lisible et exportable vers Garmin

Le modèle ne contient pas de champ `metadata` public.

## Modèle commun

Champs communs à toutes les séances :

- `sport`
- `subSport` quand utile
- `title`
- `goal`
- `description`
- `notes`
- `duration`
- `distance` optionnelle
- `intensity` / `zone` / `rpe` selon le besoin

## Sports en version enrichie

La version enrichie est réservée aux sports où la structure de séance apporte vraiment de la valeur.

V0 :

- running
- trail
- treadmill
- cycling
- indoor cycling
- swim pool
- open water swim
- rowing
- HIIT / cardio workout

Les autres activités passent en **version simple**.

## Version simple

Pour une activité simple, on conserve seulement :

- la durée
- la description
- les notes

Optionnellement, on peut garder une distance ou une cible globale si elle existe déjà dans la séance.

## Version enrichie

Une séance enrichie ajoute une structure interne de type Garmin-compatible.

### Structure de base

- `warmup`
- `main`
- `cooldown`

### Steps

Les targets et zones sont **attachées aux steps**.

Chaque step peut porter :

- une durée
- un type de durée
- un target type
- une plage de target basse/haute

Pour les intervalles :

- un intervalle contient un `activeStep`
- un `restStep` si besoin
- un `repetitionNumber`

### Course

Pour la course, on colle au plus près du modèle Garmin :

- échauffement
- blocs de travail
- récupérations
- retour au calme

Le sous-type dépend du contexte :

- road / running
- trail
- treadmill

## Exemples de cible par step

- allure
- fréquence cardiaque
- cadence
- distance
- durée
- puissance si elle est utilisée

## Mapping Garmin

### Activité enrichie

On exporte une séance structurée vers la Training API Garmin quand la structure est représentable.

### Activité simple

On exporte une séance texte avec :

- `description`
- `notes`

### Fallback

Si Garmin ne supporte pas proprement la structure d’une activité donnée, on garde la version simple.

