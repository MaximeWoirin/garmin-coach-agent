# Playbook — Weekly planning

## But

Évaluer ou ajuster une semaine d’entraînement à partir du plan et des signaux disponibles.

## Entrées utiles

- `sync-garmin` si nécessaire
- `get-fitness-state`
- `get-activities`
- `get-current-plan`
- `get-constraints`

## Séquence

1. Rafraîchir si les données sont périmées.
2. Comparer charge récente et plan prévu.
3. Identifier les contraintes actives.
4. Détecter les séances qui semblent trop ambitieuses ou trop faibles.
5. Proposer des ajustements simples.
6. Distinguer ce qui reste local (`proposed`) de ce qui doit partir vers Garmin rapidement.

## Politique d’export

- ne pas supposer que toute validation déclenche un export complet
- garder autant que possible les séances futures en `proposed`
- réserver l’export Garmin aux séances proches de l’exécution
- si une séance est déjà `exported`, préférer une logique de remplacement plutôt qu’une mutation opaque

## Sortie attendue

- vue d’ensemble de la semaine
- points de vigilance
- 1 à 3 ajustements maximum
