# Redesign épuré : Garmin Coach

Date : 2026-11-06. Révision 3 de l'atelier de recadrage (Maxime + Vibe). Remplace la révision 2 (routine dans un container).

## Intention et pourquoi

Le projet avait grandi autour d'OpenClaw : script d'installation à trois modes, 17 skills miroirs, timers systemd, crons de livraison Telegram. Ce runtime est totalement coupé et représente l'essentiel de la complexité du dépôt.

Décision de l'atelier : épurer à fond. Le projet devient une brique métier pure : CLI + MCP + des routines systemd de synchro et de publication. L'intégration dans un agent (Hermes, Vibe ou autre) viendra plus tard, en consommant le MCP ou le CLI. Aucune décision d'agent n'entre dans ce périmètre.

## Objectifs

- CLI : le coeur métier pilotable à la main (sync, contraintes, objectifs, plans, export, débriefs), installé sur la machine qui héberge la base (VM du homelab).
- MCP : la même couche métier exposée en MCP pour tout consommateur futur (agent ou autre), servi par un service systemd.
- Routines systemd : des unités et timers fournis dans le dépôt qui appellent les commandes CLI existantes :
  - synchro Garmin périodique (activités et métriques vers SQLite), toutes les heures
  - publication idempotente des séances planifiées vers Garmin, une fois par jour (matin), horizon des 7 prochains jours
- Les données structurées (contraintes, objectifs, plans, activités, débriefs) restent dans la base SQLite existante, au même endroit pour le CLI, le MCP et les routines.

## Non-objectifs

- Aucun agent, aucun playbook, aucune identité, aucune livraison Telegram dans ce périmètre.
- Pas de cerveau de planification automatique : les plans sont créés via CLI ou MCP (par Maxime aujourd'hui, par un agent demain). La routine ne fait que publier ce qui est planifié.
- Pas de container : le métier tourne nativement sur la VM du homelab, gérée en systemd.
- Pas de multi-utilisateur, pas d'interface web.
- Pas de refonte du métier Python (sync, export, SQLite) tant qu'il fait le job.

## Anti-objectifs

- Réintroduire un packaging d'agent lourd (le piège OpenClaw ne doit pas se reproduire) : pas de script d'installation interactif à trois modes, pas de venv managé généré par le dépôt, pas de gestion de timers masquée dans du code Python d'installation. Les unités systemd sont des fichiers simples posés dans le dépôt, avec une installation documentée en quelques commandes explicites.
- Multiplier les micro-outils exposés : un outil MCP = une intention, un appel CLI = une intention.

## Approches considérées

1. CLI + MCP + routines systemd (retenue). Le CLI, le MCP et les routines partagent naturellement la même base et les mêmes tokens sur la VM ; systemd est déjà la brique d'exploitation du homelab ; pas de couche de runtime supplémentaire à maintenir.
2. CLI + MCP + routine dans un container (révision 2, écartée) : un container sépare la base du poste où tourne le CLI ou impose d'y entrer ; et faire tourner un scheduler interne juste pour deux routines est une complexité sans bénéfice ici.
3. Hermes hôte unique (révision 1, écartée) : prématurée ; verrouille l'agent avant d'avoir stabilisé le métier.
4. Conserver le packaging OpenClaw (écartée) : runtime mort, complexité structurelle.

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
- Un service systemd pour le serveur MCP (transport streamable HTTP, lié en localhost par défaut ; l'exposition éventuelle vers un agent distant passera par le tunnel du homelab, hors périmètre).
- Des unités systemd dans le dépôt (dossier deploy/systemd/) :
  - garmin-coach-mcp.service : le serveur MCP
  - garmin-coach-sync.service + .timer : sync horaire (appelle sync-garmin)
  - garmin-coach-publish.service + .timer : publication quotidienne (appelle export-plan-garmin avec horizon 7 jours)
- Une configuration par fichier d'environnement (chemin DB, horizon de publication, identifiants Garmin), source par les unités.
- Persistance des identifiants de workout Garmin (nouvelle colonne garmin_workout_id en base) pour la réconciliation lors des republications et ajustements.

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
- Transport exact du MCP (port, socket systemd vs localhost TCP).
- Unités : user system vs systemctl --user, chemins exacts, environnement.
- Migration export pour update/delete (avec tests) et colonne garmin_workout_id.
- Nettoyage de la doc : README, docs/spec/agent.md, export-workflow.md.
- Découpage en jalons / PRs.

## Décisions de l'atelier

- Périmètre : CLI + MCP + routines systemd sur la VM du homelab ; agent hors périmètre, intégré plus tard via MCP.
- Publication : idempotente, réconciliée par workout_id, horizon par défaut de 7 jours.
- Routines : sync horaire + publication quotidienne, en timers systemd fournis dans le dépôt, sans installeur interactif.
- Base et données existantes : conservées, migrations additives.
