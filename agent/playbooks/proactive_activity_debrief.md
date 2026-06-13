# Playbook — Proactive activity debrief

## But

Détecter les activités récentes sans débrief complété, puis envoyer **un seul message groupé** qui demande un retour court mais exploitable.

## Entrées utiles

- `get-pending-debriefs`
- `mark-activity-debrief-prompted`
- `save-activity-debrief` (quand l'utilisateur répond plus tard)

## Séquence

1. Lire les activités à débriefer avec `get-pending-debriefs`.
2. Si rien n'est éligible : ne rien envoyer.
3. S'il y a une ou plusieurs activités éligibles : préparer **un seul message**.
4. Dans ce message, lister chaque activité brièvement pour que la réponse puisse être structurée activité par activité.
5. Demander pour chaque activité :
   - `RPE /10`
   - une note libre courte
   - toute douleur / gêne utile au suivi blessure (pendant, après, lendemain)
6. Une fois le message prêt à partir, marquer toutes les activités concernées avec `mark-activity-debrief-prompted`.

## Règles de message

- un seul message même si plusieurs activités sont en attente
- rester court, concret, pas de questionnaire lourd
- mentionner explicitement le suivi blessure
- ne pas parler de `plan_session` à l'utilisateur
- ne pas inventer d'activité si le script n'en renvoie pas

## Format recommandé

Utiliser un message du genre :

> J’ai détecté des séances à débriefer 👟
> 
> Tu peux me répondre en gardant ce format pour chaque activité :
> `RPE x/10 - note libre - douleur/gêne pendant/après/lendemain si pertinent`
> 
> À débriefer :
> - 2026-06-12 18:10 — Running — Morning Run
> - 2026-06-12 19:05 — Cycling — Ride

S'il n'y a qu'une activité, garder le même esprit mais sans faire une liste artificielle.

## Sortie attendue

- soit aucun message
- soit un seul message groupé, prêt à recevoir une réponse structurée activité par activité
