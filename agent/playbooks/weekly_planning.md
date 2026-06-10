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
- ne jamais appeler `export-plan-garmin` sans borne d'horizon par défaut
- utiliser normalement `--days-ahead` ou `--start-date` / `--end-date`
- n'exporter toute une semaine que si l'utilisateur le demande explicitement

## Choisir simple vs structuré

Au moment de créer les séances :

- utiliser une **séance simple** pour les blocs faciles à résumer en durée + intensité + note
- utiliser une **séance structurée** seulement quand le rendu Garmin des étapes compte vraiment

Pour V1, le mode structuré est surtout pertinent pour :

- `running`
- `trail`
- `treadmill`

Bon pattern recommandé :

- warmup optionnel
- bloc principal clair en `step` / `repeat`
- cooldown optionnel

Éviter de structurer pour rien :

- pas de faux JSON riche pour une séance simple
- pas de blocs abstraits qui n'apportent rien au rendu Garmin
- si la séance n'a pas besoin d'étapes lisibles sur Garmin, rester simple

## Sortie attendue

- vue d’ensemble de la semaine
- points de vigilance
- 1 à 3 ajustements maximum
