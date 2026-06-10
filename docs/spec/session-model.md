# Modèle de séance

## Objectif V1

La V1 ne cherche pas à résoudre tous les sports.

Priorité produit :
- produire de **vraies séances Garmin de course**
- propres sur Garmin Connect et sur la montre
- avec des **étapes / laps / targets** exploitables pendant l'effort

## Périmètre V1

### Sports structurés

La structure riche V1 s'applique uniquement à :

- `running`
- `trail`
- `treadmill`

### Sports simples

Tous les autres sports restent en version simple :

- durée
- intensité éventuelle
- description lisible
- export Garmin principalement textuel

Exemples hors scope structuré V1 :
- strength
- climbing
- yoga
- hiking
- mobility
- cycling
- swimming

## Principes de design

- Le modèle canonique est **orienté Garmin workout**, pas un modèle multi-sports abstrait maximaliste.
- La **source de vérité** de la séance est un JSON structuré : `session_payload_json`.
- `warmup`, `main`, `cooldown` ne sont **pas** imposés comme blocs obligatoires du schéma.
- Une séance cohérente peut contenir échauffement, bloc principal et récupération, mais cela relève de la **construction métier / skill**, pas d'une contrainte technique du format.
- Les colonnes SQL plates servent surtout à l'indexation, au filtrage simple et au workflow.

## Source de vérité

### Canonique

`session_payload_json` contient :

- le sens produit de la séance
- la structure des steps
- les conditions de fin
- les targets
- les commentaires lisibles

### Dérivé / workflow

Les colonnes SQL restent minimales et servent à :

- retrouver les séances par date / statut / activité
- afficher rapidement les listes
- suivre le workflow local et l'export Garmin

### Export Garmin

`workout_payload_json` n'est **pas** la source de vérité métier.

Son rôle visé :
- payload Garmin dérivé du `session_payload_json`
- cache / trace de la version exportable
- zone technique de compatibilité avec l'API Garmin

Donc :
- on **conçoit** une séance dans `session_payload_json`
- on **génère** ensuite `workout_payload_json` si la séance est exportable en workout structuré Garmin

## Forme canonique V1

Une séance structurée V1 est une **suite ordonnée d'items**.

Un item peut être :
- un `step`
- un `repeat`

Cela permet de représenter correctement les séances de type :
- échauffement libre
- blocs d'intervalles répétés
- récupérations
- retour au calme

## Objet top-level

Exemple de forme canonique :

```json
{
  "schemaVersion": 1,
  "sport": "running",
  "subSport": "trail",
  "format": "structured",
  "title": "6 x 800 m allure 10 km",
  "description": "Séance de seuil / allure spécifique.",
  "notes": "Rester relâché sur les 2 premières répétitions.",
  "items": []
}
```

### Champs top-level V1

- `schemaVersion`
- `sport`
- `subSport` optionnel
- `format` = `structured | simple`
- `title` optionnel
- `description` optionnel
- `notes` optionnel
- `items` pour la version structurée

## Item `step`

Un `step` représente une étape Garmin simple.

Exemple :

```json
{
  "kind": "step",
  "stepType": "warmup",
  "endCondition": {
    "type": "time",
    "valueSec": 900
  },
  "target": {
    "type": "heart_rate_zone",
    "zone": 2
  },
  "comment": "Départ facile"
}
```

### Champs V1 d'un `step`

- `kind` = `step`
- `stepType`
- `endCondition`
- `target` optionnel
- `comment` optionnel

### `stepType`

V1 doit rester simple et proche des usages Garmin running.

Types recommandés :
- `warmup`
- `run`
- `interval`
- `recovery`
- `cooldown`
- `rest`

Le skill pourra restreindre ou normaliser davantage si nécessaire.

## Item `repeat`

Un `repeat` permet d'exprimer une répétition de sous-steps.

Exemple :

```json
{
  "kind": "repeat",
  "repeatCount": 6,
  "items": [
    {
      "kind": "step",
      "stepType": "interval",
      "endCondition": {
        "type": "distance",
        "valueMeters": 800
      },
      "target": {
        "type": "pace",
        "valueSecPerKm": 255
      }
    },
    {
      "kind": "step",
      "stepType": "recovery",
      "endCondition": {
        "type": "time",
        "valueSec": 90
      }
    }
  ]
}
```

### Champs V1 d'un `repeat`

- `kind` = `repeat`
- `repeatCount`
- `items`

## Conditions de fin supportées en V1

V1 supporte uniquement les conditions validées pendant l'interview produit :

- `time`
- `distance`
- `lap_button`

### `time`

```json
{ "type": "time", "valueSec": 600 }
```

### `distance`

```json
{ "type": "distance", "valueMeters": 1000 }
```

### `lap_button`

```json
{ "type": "lap_button" }
```

Les autres formes Garmin possibles (`calories`, `heart_rate`, etc.) ne font pas partie de la V1.

## Targets supportées en V1

V1 supporte uniquement :

- `pace`
- `heart_rate_zone`

### Target allure

```json
{ "type": "pace", "valueSecPerKm": 270 }
```

### Target zone de FC

```json
{ "type": "heart_rate_zone", "zone": 3 }
```

Les autres targets possibles côté Garmin (`cadence`, `heart_rate`, `power`, `power_zone`) sont hors scope V1.

## Séances simples hors running structuré

Pour les sports hors scope V1, on garde un format simple.

Exemple :

```json
{
  "schemaVersion": 1,
  "sport": "strength",
  "format": "simple",
  "title": "Core + mobilité",
  "description": "20 min de gainage et mobilité générale.",
  "notes": "Accent sur la stabilité du tronc.",
  "simple": {
    "durationMin": 20,
    "intensity": "easy"
  }
}
```

## Conséquences stockage / architecture

### Colonnes SQL minimales visées

À terme, `plan_sessions` doit surtout garder :

- `plan_id`
- `planned_date`
- `planned_time`
- `activity_type`
- `duration_min`
- `status`
- `garmin_event_id`
- `session_payload_json`
- `workout_payload_json`
- `notes` éventuellement

### Rôle des colonnes plates existantes

Les champs plats comme :
- `intensity`
- `target_hr_low`
- `target_hr_high`
- `target_pace_sec_per_km`
- `target_rpe`

ne doivent plus porter la vérité métier de la séance structurée V1.

Ils peuvent :
- rester transitoirement pour compatibilité / lecture simple
- être dérivés du JSON quand c'est utile
- disparaître plus tard si le modèle JSON suffit

### `duration_min`

`duration_min` reste utile comme champ simple de listing / filtre.

Pour une séance structurée, sa valeur peut être :
- calculée depuis les steps quand c'est possible
- approximative / nulle si une partie importante dépend de `lap_button`

## Génération de séance cohérente

Le schéma n'impose pas une séance pédagogiquement bonne.

C'est le rôle du skill / playbook de rappeler qu'une séance de course cohérente contient souvent :

- un échauffement
- un bloc central utile à l'objectif
- une récupération / retour au calme

Autrement dit :
- le **format** reste libre et Garmin-like
- la **cohérence coaching** vit dans les règles métier

## Rendu et export

### Running / trail / treadmill

Quand `format = structured` et que le contenu respecte la V1 :
- on génère un `workout_payload_json` Garmin
- on exporte un vrai workout structuré

### Autres sports

Quand `format = simple` ou que la structure n'est pas représentable proprement :
- on garde un export simple
- le texte doit rester lisible et utile dans Garmin

## Non-objectifs V1

- couvrir tous les sports avec la même richesse
- modéliser toutes les target types Garmin
- modéliser toutes les end conditions Garmin
- imposer un énorme schéma polymorphe
- bloquer la suite du produit sur une abstraction trop générale
