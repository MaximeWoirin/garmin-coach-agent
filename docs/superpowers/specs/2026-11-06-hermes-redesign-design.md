# Redesign épuré : Garmin Coach

Date : 2026-11-06. Révision 2 de l'atelier de recadrage (Maxime + Vibe). Remplace la révision 1 (Hermes hôte unique).

## Intention et pourquoi

Le projet avait grandi autour d'OpenClaw : script d'installation à trois modes, 17 skills miroirs, timers systemd, crons de livraison Telegram. Ce runtime est totalement coupé et représente l'essentiel de la complexité du dépôt.

Décision de l'atelier : épurer à fond. Le projet devient une brique métier pure : CLI + MCP + une routine de synchro et publication automatique dans un container. L'intégration dans un agent (Hermes, Vibe ou autre) viendra plus tard, en consommant le MCP ou le CLI. Aucune décision d'agent n'entre dans ce périmètre.

## Objectifs

- CLI : le coeur métier reste pilotable à la main (sync, contraintes, objectifs, plans, export, débriefs).
- MCP : la même couche métier exposée en MCP pour tout consommateur futur (agent ou autre).
- Container : un seul container long-running qui fait tourner la routine automatique :
  - synchro Garmin périodique (activités et métriques vers SQLite)
  - publication idempotente des séances planifiées vers Garmin (scheduling sur la montre)
- Les données structurées (contraintes, objectifs, plans, activités, débriefs) restent dans la base SQLite existante.

## Non-objectifs

- Aucun agent, aucun playbook, aucune identité, aucune livraison Telegram dans ce périmètre.
- Pas de cerveau de planification automatique : les plans sont créés via CLI ou MCP (par Maxime aujourd'hui, par un agent demain). La routine ne fait que publier ce qui est planifié.
- Pas de multi-utilisateur, pas d'interface web.
- Pas de refonte du métier Python (sync, export, SQLite) tant qu'il fait le job.

## Anti-objectifs

- Réintroduire un packaging d'agent lourd (le piège OpenClaw ne doit pas se reproduire) : pas de script d'installation interactif, pas de venv managé, pas de gestion de timers systemd.
- Multiplier les micro-outils exposés : un outil MCP = une intention, un appel CLI = une intention.

## Approches considérées

1. CLI + MCP + routine container (retenue). Découple totalement le métier de l'agent ; intégration future = consommer le MCP. Aucune dépendance à un runtime d'agent ; le container est autonome et opérable partout (homelab docker/k8s, VPS).
2. Hermes hôte unique (révision 1, écartée) : prématurée ; verrouille l'agent avant d'avoir stabilisé le métier ; impose téléchargement Telegram, mémoire et cron Hermes dès maintenant.
3. Conserver le packaging OpenClaw (écartée) : runtime mort, complexité structurelle.

## Conception retenue

### Ce qui reste

- Le package garmin_coach : scripts CLI, DB, migrations, sync, plans, contraintes, objectifs, débriefs.
- Les tests et la grille qualité (couverture >= 90, mypy strict, ruff).

### Ce qui est ajouté

- Un serveur MCP fin (framework au choix du builder), exposant une dizaine d'outils grossiers, un appel = une intention, chacun déléguant au métier existant et retournant le même JSON que les scripts CLI :
  - sync_garmin, get_fitness_state, get_activities, get_current_plan
  - create_plan_draft, create_plan_session, delete_plan_session, set_plan_session_status, set_plan_status
  - get_constraints, create_constraint, set_constraint_status
  - get_goals, create_goal
  - get_pending_debriefs, save_activity_debrief, mark_activity_debrief_prompted
  - export_plan_garmin (avec dry_run), adjust_plan_garmin (mise à jour ou retrait d'une séance déjà publiée)
- Un container (Dockerfile multi-stage + image slim) contenant :
  - le serveur MCP (transport au choix du builder, ex. streamable HTTP) exposé pour tout consommateur futur
  - la routine automatique : boucle de scheduler interne ou cron de type supercronic (au choix du builder)
- La routine automatique :
  - toutes les heures : sync Garmin (activités + métriques vers SQLite)
  - une fois par jour (matin) : publication idempotente des séances planifiées de l'horizon des 7 prochains jours ; toute séance modifiée en base est réexportée, toute séance retirée est supprimée sur Garmin
- Persistance des identifiants de workout Garmin (nouvelle colonne garmin_workout_id en base) pour la réconciliation lors des republications et ajustements.
- Config par variables d'environnement (chemin DB, horaires de routine, identifiants Garmin) ; DB et tokens montés en volumes.

### Ce qui est supprimé

- Le répertoire agent/ complet (identité, skills, playbooks OpenClaw).
- scripts/install-openclaw-agent.sh et garmin_coach/install_openclaw_agent.py.
- Toutes les sections OpenClaw du README et des specs.

### Évolutions de la couche export

- La publication devient idempotente et réconciliée : republier est sûr, ajuster est sûr (mise à jour PUT workout, suppression DELETE workout et schedule), via workout-service ; montée garminconnect en 0.3.x si nécessaire.
- Le mapping sports locaux vers workout-service reste valable (docs/spec/garmin-workout-sport-mapping.md).

### Débriefs

- Les outils CLI et MCP de débrief restent (c'est du métier : qui attend un débrief, le sauver, le marquer sollicité), mais aucune sollicitation proactive : ce déclenchement reviendra à l'agent futur.

## Resté au builder

- Choix du framework MCP et nommage exact des outils.
- Structure du module serveur MCP et gestion des sessions DB.
- Choix du scheduler interne (boucle vs supercronic) et des horaires par défaut.
- Transport MCP (stdio local vs HTTP exposé) et ports.
- Migration export pour update/delete (avec tests) et colonne garmin_workout_id.
- Nettoyage de la doc : README, docs/spec/agent.md, export-workflow.md.
- Découpage en jalons / PRs.

## Décisions de l'atelier

- Périmètre : CLI + MCP + routine container ; agent hors périmètre, intégré plus tard via MCP.
- Publication : idempotente, réconciliée par workout_id, horizon par défaut de 7 jours.
- Routine : sync horaire + publication quotidienne, dans un seul container.
- Base et données existantes : conservées, migrations additives.
