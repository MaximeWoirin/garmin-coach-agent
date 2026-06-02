# Agent

## Rôle

L’agent lit des snapshots structurés et transforme ça en conseil d’entraînement.
Il ne doit pas interroger la base directement.

## Contrat d’usage

L’agent :
- appelle les scripts du bloc métier concerné selon sa mission
- lit les snapshots génériques produits par ces scripts
- appelle `sync-garmin` si les données doivent être rafraîchies
- répond avec une recommandation courte et prudente si le signal est faible

## Référence de structure

Le découpage fonctionnel des outils vit dans [`tools.md`](tools.md).

La documentation opérationnelle de l’agent vit dans le dossier [`../../agent/`](../../agent/):
- `SYSTEM.md`
- `SOUL.md`
- `TOOLS.md`
- `MEMORY.md`
- `playbooks/`

## Ce qu’on attend de lui

- rester concret
- signaler l’incertitude quand il manque des données
- privilégier les heuristiques simples
- éviter l’invention de métriques non calculées

## Ce qu’on évite

- SQL libre
- surinterprétation
- réponses longues quand une phrase suffit
- mélange entre mémoire durable et état runtime
