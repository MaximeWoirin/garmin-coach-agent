# Mapping Garmin des sports de workout

## But

Documenter le vrai mapping à utiliser quand on crée un **workout Garmin**.

Point critique :

- les ids de `activity-service/activityTypes` servent aux **activités Garmin**
- les ids de `workout-service` servent aux **workouts Garmin**
- ces deux espaces de types **ne sont pas interchangeables**

C’est précisément ce qui a causé le bug où une séance locale `strength` apparaissait comme `swimming` sur Garmin.

## Méthode de validation

Tests observés le `2026-06-09` via une session Garmin Connect web authentifiée.

Méthode utilisée :

1. création d’un workout temporaire via `POST /gc-api/workout-service/workout`
2. lecture immédiate via `GET /gc-api/workout-service/workout/{id}`
3. suppression via `DELETE /gc-api/workout-service/workout/{id}`

On retient la **normalisation renvoyée par Garmin** comme source de vérité pratique.

## Mapping observé du workout-service

| workout-service `sportTypeId` | `sportTypeKey` normalisé | Statut |
|---|---|---|
| 1 | `running` | validé |
| 2 | `cycling` | validé |
| 3 | `other` | validé |
| 4 | `swimming` | validé |
| 5 | `strength_training` | validé |
| 6 | `cardio_training` | validé |
| 7 | `yoga` | validé |
| 8 | `pilates` | validé |
| 9 | `hiit` | validé |
| 10 | `multi_sport` | validé avec payload multi-segments |
| 11 | `mobility` | validé |
| 12 | `walking` | validé |
| 13 | `rucking` | validé |

## Contre-exemples importants

Les ids d’`activity-service` ne doivent pas être réutilisés tels quels pour créer des workouts.

Exemples observés :

| Entrée envoyée au workout-service | Résultat Garmin |
|---|---|
| `{"sportTypeId": 4, "sportTypeKey": "strength_training"}` | normalisé en `swimming` |
| `{"sportTypeId": 5, "sportTypeKey": "swimming"}` | normalisé en `strength_training` |
| `{"sportTypeId": 9, "sportTypeKey": "walking"}` | normalisé en `hiit` |
| `{"sportTypeId": 13, "sportTypeKey": "strength_training"}` | normalisé en `rucking` |
| `{"sportTypeId": 28, "sportTypeKey": "yoga"}` | normalisé en type nul / non reconnu |
| `{"sportTypeId": 26, "sportTypeKey": "swimming"}` | normalisé en type nul / non reconnu |
| `{"sportTypeId": 139, "sportTypeKey": "rock_climbing"}` | normalisé en type nul / non reconnu |

## Conséquences produit

### À utiliser directement

- `running` → `1 / running`
- `cycling` → `2 / cycling`
- `swimming` → `4 / swimming`
- `strength` → `5 / strength_training`
- `cardio` → `6 / cardio_training`
- `yoga` → `7 / yoga`
- `pilates` → `8 / pilates`
- `hiit` → `9 / hiit`
- `mobility` → `11 / mobility`
- `walking` → `12 / walking`
- `rucking` → `13 / rucking`

### Sports locaux sans type workout Garmin fiable

Certains sports existent côté activités Garmin mais pas comme type de workout simple exploitable ici.

Cas observés :

- `hiking`
- `climbing`
- `rock_climbing`
- `indoor_climbing`

Pour ces cas, il faut choisir un fallback produit explicite au lieu de réutiliser naïvement l’id d’activité Garmin.

Choix actuel dans ce repo :

- `hiking` → fallback `walking`
- `climbing` → fallback `other`

## Différence activité vs workout

Exemples d’ids côté `activity-service/activityTypes` :

- `9 = walking`
- `13 = strength_training`
- `26 = swimming`
- `163 = yoga`
- `139 = rock_climbing`

Ces ids sont cohérents pour des **activités Garmin enregistrées**,
mais pas pour la création de **workouts Garmin**.

## Règle de sécurité

Quand un sport local n’a pas de mapping workout Garmin observé et stable :

- ne pas deviner à partir d’`activity-service/activityTypes`
- préférer un fallback explicite (`other`, `walking`, etc.)
- documenter le choix dans ce fichier
