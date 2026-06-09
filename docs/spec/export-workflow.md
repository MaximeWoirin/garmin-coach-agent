# Workflow d'export Garmin

## But

Découpler :
- la validation locale du plan
- la publication des séances vers Garmin

Le but est de garder un plan hebdomadaire adaptable en cours de semaine, sans rendre impossible l'édition dès qu'une validation a eu lieu.

## Principe

On sépare trois couches :

1. **Édition locale**
   - le plan se construit et se corrige localement
2. **Validation locale**
   - le plan est considéré comme bon côté produit / coach
3. **Publication Garmin**
   - seules certaines séances sont effectivement poussées vers Garmin
   - la publication est pilotée **au niveau session** (pas au niveau plan)

La publication suit le modèle de séance :

- **séance simple** → export texte via `description` / `notes`
- **séance enrichie** → export structuré si Garmin le permet

Le choix du `sportType` Garmin doit suivre le mapping validé dans [`garmin-workout-sport-mapping.md`](garmin-workout-sport-mapping.md), pas les ids d’`activity-service`.


## États de référence

### Plan (cycle de vie local uniquement)
- `draft` — brouillon local
- `active` — plan validé localement
- `archived` — plan clos

Le statut de plan ne porte pas l'état de publication Garmin.
La publication est suivie au niveau session.

### Session
- `draft` — brouillon local, pas encore validée
- `proposed` — validée localement, prête à être publiée, encore éditable
- `exported` — publiée vers Garmin, non modifiable
- `done` — réalisée / réconciliée
- `skipped` — non réalisée
- `canceled` — annulée

## Workflow recommandé

### 1. Construction du plan
- création du plan en `draft`
- création / édition des séances en `draft`

### 2. Validation locale
Quand la semaine est prête :
- le plan passe `draft -> active`
- les séances concernées passent `draft -> proposed`

À ce stade :
- le plan est validé localement
- Garmin n'a pas encore reçu les séances
- aucun export implicite n'a lieu

### 3. Publication Garmin progressive (last minute)
L'export est traité comme un workflow de publication séparé.

On exporte seulement les séances `proposed` qui deviennent concrètes, par exemple :
- aujourd'hui
- demain
- éventuellement horizon court (`J+2`)

Les autres séances restent `proposed`, donc encore facilement adaptables.

Options de filtrage :
- `--start-date` / `--end-date` : plage de dates explicite
- `--days-ahead` : horizon court à partir d'aujourd'hui

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

## Règles d'adaptation (V1)

### Séance `proposed`
Elle est encore locale.
On peut :
- la supprimer via `delete-plan-session`
- recréer une nouvelle séance via `create-plan-session`

L'adaptation se fait **avant export**, grâce au mode progressif / last minute.

### Séance `exported`
Elle n'est plus modifiable.
On ne peut pas la supprimer ni la muter.
Le workflow V1 évite ce besoin grâce à l'export last minute.

Autrement dit :
- `proposed` = éditable (delete + recreate)
- `exported` = verrouillée

### Pas de `update-plan-session` en V1
L'adaptation passe par `delete-plan-session` + `create-plan-session` tant que la séance est `proposed`.

### Pas de `replace-plan-session` en V1
Le remplacement d'une séance déjà exportée n'est pas supporté dans cette version.

## Outils impliqués

### Validation locale
- `create-plan-draft`
- `create-plan-session`
- `delete-plan-session`
- `set-plan-status` (validation locale / clôture uniquement)
- `set-plan-session-status`

### Publication Garmin
- `export-plan-garmin` (export progressif, séances `proposed` uniquement)

### Réconciliation
- `sync-garmin`
- `get-current-plan`
- `get-activities`
- `get-fitness-state`
- `get-constraints`

## Politique recommandée

### Manuel d'abord
Au début, on peut garder un export manuel :
- validation locale du plan
- export Garmin explicite quand nécessaire

### Puis auto sur horizon court
Ensuite, un cron peut publier automatiquement :
- les séances `proposed`
- sur un horizon court seulement

C'est le meilleur compromis entre :
- contrôle
- simplicité
- adaptabilité en cours de semaine
