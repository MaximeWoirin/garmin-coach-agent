# Redesign épuré : Garmin Coach

Date : 2026-11-06. Révision 6 de l'atelier de recadrage (Maxime + Vibe). Version finale.

## Intention et pourquoi

Le projet avait grandi autour d'OpenClaw : script d'installation à trois modes, 17 skills miroirs, timers systemd dédiés, crons de livraison Telegram. Ce runtime est totalement coupé et représente l'essentiel de la complexité du dépôt.

Décision de l'atelier : épurer à fond, avec un découplage net des responsabilités. Le projet devient trois composants autour d'un noyau :

- un noyau Python : bibliothèque métier (interactions Garmin + DB), sans aucun protocole dedans ;
- un composant MCP à part : un process séparé, adaptateur fin qui déclenche la logique Python (lister les séances, publier un entraînement, etc.) ;
- systemd comme scheduler : des timers qui déclenchent la logique métier Python par un runner interne.

Les trois s'appuient sur la même bibliothèque ; toute la flexibilité d'usage vient de là. L'intégration dans un agent (Hermes, Vibe ou autre) viendra plus tard, en consommant le MCP. Aucune décision d'agent n'entre dans ce périmètre.

## Objectifs

- Noyau : garmin_coach comme bibliothèque métier pure (Garmin + SQLite), seule à contenir la logique et les accès base.
- MCP : seule surface de consultation et d'action (humain, script, agent futur), process séparé, adaptateur fin sans logique.
- Routines : timers systemd qui exécutent le runner interne pour la synchro Garmin (toutes les heures) et la publication idempotente des séances planifiées (une fois par jour le matin, horizon des 7 prochains jours).
- Règle d'or : MCP et runner appellent exactement les mêmes fonctions de la bibliothèque, testées une seule fois.
- Packaging : une seule image container, plusieurs points d'entrée (serve pour le MCP, sync et publish pour le runner), DB et tokens en volume partagé ; systemd lance le container en service et l'utilise pour ses timers.
- Les données structurées (contraintes, objectifs, plans, activités, débriefs) restent dans la base SQLite existante.

## Non-objectifs

- Aucun agent, aucun playbook, aucune identité, aucune livraison Telegram dans ce périmètre.
- Pas de cerveau de planification automatique : les plans sont créés via MCP (par Maxime aujourd'hui, par un agent demain). La routine ne fait que publier ce qui est planifié.
- Pas de CLI utilisateur : plus d'entry points console documentés ; le runner interne est de la plomberie d'exploitation, il n'est pas une surface d'usage.
- Pas de microservice : pas d'API HTTP interne autour du noyau ; le découplage est au niveau des composants (bibliothèque + adaptateurs fins), pas des processus qui se parlent en réseau.
- Pas de scheduler interne : les routines sont déclenchées par systemd, pas par une boucle dans le serveur.
- Pas de multi-utilisateur, pas d'interface web.
- Pas de refonte du métier Python (sync, export, SQLite) tant qu'il fait le job.

## Anti-objectifs

- Réintroduire un packaging d'agent lourd (le piège OpenClaw ne doit pas se reproduire) : pas de script d'installation interactif, pas de venv managé, pas de gestion de timers masquée dans du code Python d'installation.
- Multiplier les micro-outils : un outil MCP = une intention.
- Dupliquer la logique : une seule implémentation du métier, autant de déclencheurs que nécessaire.

## Approches considérées

1. Bibliothèque + adaptateurs fins MCP et systemd (retenue). Le découplage demandé par l'atelier, sans le coût du microservice : chaque composant a une seule responsabilité, la bibliothèque reste testable et consommable partout, et il n'y a ni contrat interne ni service de plus à opérer.
2. Vrai microservice : noyau en API HTTP, MCP et scheduler clients (écartée). Deux services à opérer, un contrat interne à maintenir, de la sérialisation et du retry, pour deux consommateurs qui vivent sur la même machine ; la flexibilité viendrait de la bibliothèque propre, pas de l'isolation de processus.
3. Tout dans un seul process : serveur MCP avec scheduler interne (révision 5, écartée). Fonctionne, mais mélange les responsabilités et rend le serveur propriétaire des routines.
4. Timers systemd qui déclenchent le MCP en HTTP (écartée) : de la plomberie fragile pour un handshake de protocole, alors qu'appeler la bibliothèque est direct.
5. Conserver le packaging OpenClaw (écartée) : runtime mort, complexité structurelle.

## Conception retenue

### Ce qui reste

- Le package garmin_coach comme bibliothèque métier : DB, migrations, sync, plans, contraintes, objectifs, débriefs, export.
- Les tests et la grille qualité (couverture >= 90, mypy strict, ruff).

### Structure des composants

- garmin_coach/ : le noyau. Interactions Garmin, DB, migrations, toute la logique. Aucune dépendance à un protocole (ni MCP, ni HTTP, ni argparse).
- Le serveur MCP : composant à part, process dédié, adaptateur fin. Transport streamable HTTP, lié en localhost par défaut ; l'exposition vers un agent distant passera par le tunnel du homelab, hors périmètre.
- Le runner interne : deux commandes minimales (sync, publish), invocables par systemd uniquement, qui appellent les fonctions du noyau.

### Le MCP

Une dizaine d'outils grossiers, un appel = une intention, déléguant au noyau :

- sync_garmin, get_fitness_state, get_activities, get_current_plan
- create_plan_draft, create_plan_session, delete_plan_session, set_plan_session_status, set_plan_status
- get_constraints, create_constraint, set_constraint_status
- get_goals, create_goal
- get_pending_debriefs, save_activity_debrief, mark_activity_debrief_prompted
- export_plan_garmin (avec dry_run), adjust_plan_garmin (mise à jour ou retrait d'une séance déjà publiée)

### Les routines systemd

- garmin-coach-sync.timer : toutes les heures, déclenche le runner sync (synchro des activités et métriques vers SQLite).
- garmin-coach-publish.timer : une fois par jour (matin), déclenche le runner publish (export idempotent des séances planifiées, horizon 7 jours config par environnement).
- Le runner journalise chaque résultat ; l'échec d'une routine est visible dans journald.

### Packaging

- Une seule image container (Dockerfile multi-stage, image finale slim, utilisateur non root) avec plusieurs points d'entrée :
  - serve : démarre le serveur MCP (utilisé par garmin-coach.service, service systemd dédié)
  - sync et publish : exécutent le runner puis terminent (utilisés par les timers)
- DB SQLite et tokens Garmin montés en volume ; configuration par variables d'environnement ; healthcheck sur l'endpoint MCP.
- SQLite en mode WAL pour accepter les accès concurrents du MCP et des timers (locks brefs à cette échelle, acceptable).

### Ce qui est supprimé

- Le répertoire agent/ complet (identité, skills, playbooks OpenClaw).
- scripts/install-openclaw-agent.sh et garmin_coach/install_openclaw_agent.py.
- Les entry points console ([project.scripts]) et les frontends argparse ; les fonctions métier migrent en bibliothèque.
- Toutes les sections OpenClaw et CLI du README et des specs.

### Évolutions de la couche export

- La publication devient idempotente et réconciliée : republier est sûr, ajuster est sûr (mise à jour PUT workout, suppression DELETE workout et schedule), via workout-service ; montée garminconnect en 0.3.x si nécessaire.
- Le mapping sports locaux vers workout-service reste valable (docs/spec/garmin-workout-sport-mapping.md).

### Débriefs

- Les outils MCP de débrief restent (métier : qui attend un débrief, le sauver, le marquer sollicité), mais aucune sollicitation proactive : ce déclenchement reviendra à l'agent futur.

## Resté au builder

- Choix du framework MCP et nommage exact des outils.
- Structure du module serveur MCP et gestion des sessions DB.
- Détails du runner (signature des commandes, codes de sortie pour systemd).
- Détails du Dockerfile (image de base, multi-entrée).
- Migration export pour update/delete et colonne garmin_workout_id.
- Migration du métier scripts vers bibliothèque et adaptation des tests.
- Nettoyage de la doc : README, docs/spec/agent.md, docs/spec/scripts.md, export-workflow.md.

## Décisions de l'atelier

- Architecture : bibliothèque noyau + adaptateurs fins (MCP à part, systemd scheduler), pas de microservice, pas de scheduler interne.
- MCP : seule surface d'usage ; le runner interne est réservé à l'exploitation.
- Publication : idempotente, réconciliée par workout_id, horizon par défaut de 7 jours.
- Routines : sync horaire + publication quotidienne, en timers systemd, via le runner.
- Packaging : une image, plusieurs points d'entrée, DB et tokens en volume.
- Base et données existantes : conservées, migrations additives.
