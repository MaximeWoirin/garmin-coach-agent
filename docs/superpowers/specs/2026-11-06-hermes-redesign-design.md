# Redesign épuré : Garmin Coach

Date : 2026-11-06. Révision 5 de l'atelier de recadrage (Maxime + Vibe). Version finale.

## Intention et pourquoi

Le projet avait grandi autour d'OpenClaw : script d'installation à trois modes, 17 skills miroirs, timers systemd dédiés, crons de livraison Telegram. Ce runtime est totalement coupé et représente l'essentiel de la complexité du dépôt.

Décision de l'atelier : épurer à fond. Le projet se résume à trois choses : remettre à plat la base de code Python, la surcoucher avec un MCP, et packager le tout dans un container. Le MCP est la seule surface : tout se fait via MCP, y compris les routines automatisées, qui tournent dans le scheduler interne du container. L'intégration dans un agent (Hermes, Vibe ou autre) viendra plus tard, en consommant le MCP. Aucune décision d'agent n'entre dans ce périmètre.

## Objectifs

- MCP unique : tous les usages passent par le serveur MCP (humain, script, agent, routines internes).
- Le container embarque le serveur MCP et un scheduler interne :
  - synchro Garmin périodique (activités et métriques vers SQLite), toutes les heures
  - publication idempotente des séances planifiées vers Garmin, une fois par jour (matin), horizon des 7 prochains jours
- Sur l'hôte (VM du homelab), systemd se limite à lancer le container en service.
- Les données structurées (contraintes, objectifs, plans, activités, débriefs) restent dans la base SQLite existante, montée en volume avec les tokens Garmin.

## Non-objectifs

- Aucun agent, aucun playbook, aucune identité, aucune livraison Telegram dans ce périmètre.
- Pas de cerveau de planification automatique : les plans sont créés via MCP (par Maxime aujourd'hui, par un agent demain). La routine ne fait que publier ce qui est planifié.
- Pas de CLI : plus aucun entry point console ; aucun usage documenté en ligne de commande.
- Pas de timers systemd : les routines vivent dans le scheduler du container ; systemd ne lance que le container.
- Pas de multi-utilisateur, pas d'interface web.
- Pas de refonte du métier Python (sync, export, SQLite) tant qu'il fait le job : les fonctions derrière les anciens scripts restent, en bibliothèque, appelées par les outils MCP.

## Anti-objectifs

- Réintroduire un packaging d'agent lourd (le piège OpenClaw ne doit pas se reproduire) : pas de script d'installation interactif, pas de venv managé, pas de gestion de timers dans du code d'installation.
- Multiplier les micro-outils : un outil MCP = une intention.
- Dupliquer les points d'entrée : une seule surface, le MCP. Même les routines passent par le même code.

## Approches considérées

1. MCP unique + scheduler interne + container, systemd lance le container (retenue). Interface unique en HTTP dans un package autonome, déployable tel quel sur la VM, réutilisable plus tard depuis n'importe quel agent. L'objection container de la révision 2 tombait avec le CLI ; sans CLI, le container redevient le packaging le plus simple.
2. Timers systemd qui déclenchent les outils MCP du container (écartée) : de la plomberie d'hôte en plus pour deux routines ; le scheduler interne rend le container autonome et le comportement identique en dev et en prod.
3. CLI + MCP (écartée) : deux surfaces pour le même métier.
4. Hermes hôte unique (écartée) : prématurée ; verrouille l'agent avant d'avoir stabilisé le métier.
5. Conserver le packaging OpenClaw (écartée) : runtime mort, complexité structurelle.

## Conception retenue

### Ce qui reste

- Le package garmin_coach comme bibliothèque métier : DB, migrations, sync, plans, contraintes, objectifs, débriefs, export.
- Les tests et la grille qualité (couverture >= 90, mypy strict, ruff).

### Ce qui est ajouté

- Un serveur MCP fin (framework au choix du builder), seule surface, exposant une dizaine d'outils grossiers, un appel = une intention, déléguant au métier :
  - sync_garmin, get_fitness_state, get_activities, get_current_plan
  - create_plan_draft, create_plan_session, delete_plan_session, set_plan_session_status, set_plan_status
  - get_constraints, create_constraint, set_constraint_status
  - get_goals, create_goal
  - get_pending_debriefs, save_activity_debrief, mark_activity_debrief_prompted
  - export_plan_garmin (avec dry_run), adjust_plan_garmin (mise à jour ou retrait d'une séance déjà publiée)
- Un scheduler interne (boucle asyncio dans le process du serveur) qui appelle les mêmes fonctions que les outils MCP :
  - toutes les heures : sync_garmin
  - une fois par jour (matin) : export_plan_garmin (horizon 7 jours)
- Un container (Dockerfile multi-stage, image finale slim) : entrypoint unique qui démarre serveur MCP + scheduler ; config par variables d'environnement ; DB et tokens montés en volumes ; healthcheck sur l'endpoint MCP.
- Côté hôte : une seule unité systemd (garmin-coach.service) qui lance le container ; Dockerfile Compose ou docker run documentés en quelques commandes.

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
- Détails du scheduler (asyncio simple, retry, journalisation d'échec de routine).
- Détails du Dockerfile (image de base, utilisateur non root).
- Migration export pour update/delete et colonne garmin_workout_id.
- Migration du métier scripts vers bibliothèque et adaptation des tests.
- Nettoyage de la doc : README, docs/spec/agent.md, docs/spec/scripts.md, export-workflow.md.
- Découpage en jalons / PRs.

## Décisions de l'atelier

- Périmètre : bibliothèque Python remise à plat + MCP unique + container autonome (serveur + scheduler) ; systemd sur l'hôte se limite à lancer le container.
- Publication : idempotente, réconciliée par workout_id, horizon par défaut de 7 jours.
- Routines : sync horaire + publication quotidienne, dans le scheduler interne du container.
- Base et données existantes : conservées, migrations additives.
