# Workflow d’export Garmin

## But

Découpler :
- la validation locale du plan
- la publication des séances vers Garmin

Le but est de garder un plan hebdomadaire adaptable en cours de semaine, sans rendre impossible l’édition dès qu’une validation a eu lieu.

## Principe

On sépare trois couches :

1. **Édition locale**
   - le plan se construit et se corrige localement
2. **Validation locale**
   - le plan est considéré comme bon côté produit / coach
3. **Publication Garmin**
   - seules certaines séances sont effectivement poussées vers Garmin

## États de référence

### Plan
- `draft` — brouillon local
- `active` — plan validé localement et vivant
- `sent` — plan considéré comme publié côté workflow historique
- `archived` — plan clos

### Session
- `draft` — brouillon local
- `proposed` — validée localement, prête à être publiée
- `exported` — publiée vers Garmin
- `done` — réalisée / réconciliée
- `skipped` — non réalisée
- `canceled` — annulée / remplacée

## Workflow recommandé (option C)

### 1. Construction du plan
- création du plan en `draft`
- création / édition des séances en `draft`

### 2. Validation locale
Quand la semaine est prête :
- le plan passe `draft -> active`
- les séances concernées passent `draft -> proposed`

À ce stade :
- le plan est validé localement
- Garmin n’a pas encore forcément reçu toutes les séances

### 3. Publication Garmin progressive
L’export est traité comme un workflow de publication séparé.

On exporte seulement les séances `proposed` qui deviennent concrètes, par exemple :
- aujourd’hui
- demain
- éventuellement horizon court (`J+2`)

Les autres séances restent `proposed`, donc encore facilement adaptables.

### 4. Réconciliation du réel
Après exécution réelle :
- `sync-garmin` importe activités et métriques
- le système rapproche le réalisé du plan
- les séances peuvent passer à `done`

## Pourquoi ce workflow

Si validation = export immédiat de toute la semaine, alors :
- une adaptation de milieu de semaine devient pénible
- une séance déjà exportée ne doit pas être modifiée brutalement
- on perd en souplesse sur le vivant

Avec ce workflow :
- le plan hebdo est validé tôt
- seules les séances proches sont publiées
- le milieu / la fin de semaine restent ajustables

## Règles d’adaptation

### Séance `proposed`
Elle est encore locale.
On peut :
- la modifier
- la supprimer
- la déplacer
- la remplacer

### Séance `exported`
Elle n’est plus librement éditable.
Le workflow recommandé est :
- annuler / marquer remplacée l’ancienne séance
- créer une nouvelle séance de remplacement en `proposed`
- publier ensuite cette nouvelle séance

Autrement dit :
- `proposed` = éditable
- `exported` = remplaçable, pas mutable librement

## Outils actuels impliqués

### Validation locale
- `create-plan-draft`
- `create-plan-session`
- `delete-plan-session`
- `set-plan-status`
- `set-plan-session-status`

### Publication Garmin
- `export-plan-garmin`

### Réconciliation
- `sync-garmin`
- `get-current-plan`
- `get-activities`
- `get-fitness-state`
- `get-constraints`

## Outils à ajouter pour bien supporter ce workflow

### `update-plan-session`
But : modifier une séance encore locale (`draft` ou `proposed`) sans passer par delete + recreate.

### `replace-plan-session`
But : remplacer proprement une séance déjà `exported`.

Comportement cible :
- ancienne séance marquée `canceled` ou `superseded`
- nouvelle séance créée en `proposed`
- export explicite ensuite

### Évolution de `export-plan-garmin`
À terme, il devrait pouvoir filtrer explicitement les séances à publier, par exemple :
- horizon court
- plage de dates
- seulement les séances `proposed`

## Politique recommandée

### Manuel d’abord
Au début, on peut garder un export manuel :
- validation locale du plan
- export Garmin explicite quand nécessaire

### Puis auto sur horizon court
Ensuite, un cron peut publier automatiquement :
- les séances `proposed`
- sur un horizon court seulement

C’est le meilleur compromis entre :
- contrôle
- simplicité
- adaptabilité en cours de semaine
