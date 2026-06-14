# Playbook — Constraint cleanup

## But

Faire un récap hebdomadaire des contraintes actives, signaler celles qui semblent à nettoyer, puis demander confirmation avant toute mutation.

## Entrées utiles

- `get-constraint-cleanup`
- `set-constraint-status` (seulement après confirmation explicite)

## Séquence

1. Lire l’état courant avec `get-constraint-cleanup`.
2. S’il n’y a aucune contrainte active : dire qu’il n’y a rien à relire cette semaine.
3. S’il y a des contraintes actives mais aucune candidate au ménage : envoyer un récap court, sans pousser à archiver artificiellement.
4. S’il y a des candidates au ménage :
   - lister brièvement toutes les contraintes actives
   - regrouper clairement les candidates avec leur raison
   - demander si certaines doivent passer en `inactive`
5. Ne changer aucun statut tant que l’utilisateur n’a pas confirmé précisément quoi archiver.

## Règles de message

- rester très concis
- parler métier, pas heuristiques internes
- ne pas inventer de raison absente du JSON
- ne pas archiver automatiquement

## Format recommandé

> Récap ménage contraintes
>
> Actives : 8
> À relire cette semaine : 2
>
> Actives :
> - #7 availability/training — Vacances prévues début septembre
> - #10 schedule/training — Semaine très chaude du 15 au 21 juin
>
> Candidates au ménage :
> - #7 — confiance faible
> - #10 — expirée
>
> Tu veux que je passe certaines contraintes en inactive ?
