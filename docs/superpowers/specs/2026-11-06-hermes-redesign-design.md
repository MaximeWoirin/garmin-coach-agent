# Redesign épuré : Garmin Coach

Date : 2026-11-06. Révision 4 de l'atelier de recadrage (Maxime + Vibe). Remplace la révision 3 (CLI + MCP + systemd).

## Intention et pourquoi

Le projet avait grandi autour d'OpenClaw : script d'installation à trois modes, 17 skills miroirs, timers systemd, crons de livraison Telegram. Ce runtime est totalement coupé et représente l'essentiel de la complexité du dépôt.

Décision de l'atelier : épurer à fond. Le projet devient une brique métier pure avec une seule surface : le MCP. Tout se fait via MCP : consultation, création de plans, contraintes, objectifs, débriefs, synchro, publication. Les entry points CLI disparaissent entièrement. L'intégration dans un agent (Hermes, Vibe ou autre) viendra plus tard, en consommant le MCP. Aucune décision d'agent n'entre dans ce périmètre.

## Objectifs

- MCP unique : tous les usages passent par le serveur MCP, qu'ils viennent d'un humain, d'un script, d'un agent ou des routines.
- Le serveur MCP est servi par un service systemd sur la VM du homelab, là où vivent la base SQLite et les tokens Garmin.
- Routines systemd : des timers appellent les outils MCP :
  - synchro Garmin périodique (activités et métriques vers SQLite), toutes les heures
  - publication idempotente des séances planifiées vers Garmin, une fois par jour (matin), horizon des 7 prochains jours
- Les données structurées (contraintes, objectifs, plans, activités, débriefs) restent dans la base SQLite existante.

## Non-objectifs

- Aucun agent, aucun playbook, aucune identité, aucune livraison Telegram dans ce périmètre.
- Pas de cerveau de planification automatique : les plans sont créés via MCP (par Maxime aujourd'hui, par un agent demain). La routine ne fait que publier ce qui est planifié.
- Pas de CLI : les scripts console ([project.scripts]) sont supprimés ; aucun usage n'est documenté en ligne de commande.
- Pas de container.
- Pas de multi-utilisateur, pas d'interface web.
- Pas de refonte du métier Python (sync, export, SQLite) tant qu'il fait le job : les fonctions derrière les anciens scripts restent, ce sont des fonctions de bibliothèque appelées par les outils MCP.

## Anti-objectifs

- Réintroduire un packaging d'agent lourd (le piège OpenClaw ne doit pas se reproduire) : pas de script d'installation interactif à trois modes, pas de venv managé généré par le dépôt, pas de gestion de timers masquée dans du code Python d'installation. Les unités systemd sont des fichiers simples posés dans le dépôt, avec une installation documentée en quelques commandes explicites.
- Multiplier les micro-outils exposés : un outil MCP = une intention.
- Dupliquer les points d'entrée : une seule surface, le MCP. Même les routines passent par le même code.

## Approches considérées

1. MCP unique + routines systemd (retenue). Une seule surface à maintenir, à tester et à documenter ; les routines déclenchent exactement le même code que n'importe quel consommateur ; prêt pour un agent futur sans rien réécrire.
2. CLI + MCP (révision 3, écartée) : deux surfaces pour le même métier, deux docs, deux tests d'usage ; le CLI n'a plus d'usage propre une fois les routines automatisées.
3. CLI + MCP + routine dans un container (révision 2, écartée) : complexité de runtime sans bénéfice.
4. Hermes hôte unique (révision 1, écartée) : prématurée ; verrouille l'agent avant d'avoir stabilisé le métier.
5. Conserver le packaging OpenClaw (écartée) : runtime mort, complexité structurelle.

## Conception retenue

### Ce qui reste

- Le package garmin_coach comme bibliothèque métier : DB, migrations, sync, plans, contraintes, objectifs, débriefs, export. Les fonctions derrière les anciens scripts CLI restent, en tant que bibliothèque.
- Les tests et la grille qualité (couverture >= 90, mypy strict, ruff).

### Ce qui est ajouté

- Un serveur MCP fin (framework au choix du builder), seule surface du projet, exposant une dizaine d'outils grossiers, un appel = une intention, chacun déléguant au métier existant :
  - sync_garmin, get_fitness_state, get_activities, get_current_plan
  - create_plan_draft, create_plan_session, delete_plan_session, set_plan_session_status, set_plan_status
  - get_constraints, create_constraint, set_constraint_status
  - get_goals, create_goal
  - get_pending_debriefs, save_activity_debrief, mark_activity_debrief_prompted
  - export_plan_garmin (avec dry_run), adjust_plan_garmin (mise à jour ou retrait d'une séance déjà publiée)
- Un service systemd pour le serveur MCP (transport streamable HTTP, lié en localhost par défaut ; l'exposition éventuelle vers un agent distant passera par le tunnel du homelab, hors périmètre).
- Des timers systemd dans le dépôt (dossier deploy/systemd/) qui déclenchent les outils MCP :
  - garmin-coach-sync.timer : toutes les heures, déclenche sync_garmin
  - garmin-coach-publish.timer : une fois par jour (matin), déclenche export_plan_garmin (horizon 7 jours)
  Le mécanisme de déclenchement (mini-runner interne réservé aux timers qui appelle les fonctions serveur, ou appel HTTP local au MCP) est laissé au builder ; dans les deux cas il n'y a aucune surface CLI documentée et le code exécuté est celui des outils MCP.
- Une configuration par fichier d'environnement (chemin DB, horizon de publication, identifiants Garmin), source par les unités.
- Persistance des identifiants de workout Garmin (nouvelle colonne garmin_workout_id en base) pour la réconciliation lors des republications et ajustements.

### Ce qui est supprimé

- Le répertoire agent/ complet (identité, skills, playbooks OpenClaw).
- scripts/install-openclaw-agent.sh et garmin_coach/install_openclaw_agent.py.
- Les entry points console ([project.scripts] du pyproject) et les modules *scripts* correspondants ; les fonctions métier migrent en bibliothèque.
- Toutes les sections OpenClaw et CLI du README et des specs.

### Évolutions de la couche export

- La publication devient idempotente et réconciliée : republier est sûr, ajuster est sûr (mise à jour PUT workout, suppression DELETE workout et schedule), via workout-service ; montée garminconnect en 0.3.x si nécessaire.
- Le mapping sports locaux vers workout-service reste valable (docs/spec/garmin-workout-sport-mapping.md).

### Débriefs

- Les outils MCP de débrief restent (c'est du métier : qui attend un débrief, le sauver, le marquer sollicité), mais aucune sollicitation proactive : ce déclenchement reviendra à l'agent futur.

## Resté au builder

- Choix du framework MCP et nommage exact des outils.
- Structure du module serveur MCP et gestion des sessions DB.
- Transport exact du MCP (port, socket systemd vs localhost TCP).
- Mécanisme de déclenchement des timers (mini-runner interne vs appel HTTP local au MCP).
- Migration du métier : transformer les modules scripts en bibliothèque, adapter les tests.
- Migration export pour update/delete (avec tests) et colonne garmin_workout_id.
- Nettoyage de la doc : README, docs/spec/agent.md, docs/spec/scripts.md, export-workflow.md.
- Découpage en jalons / PRs.

## Décisions de l'atelier

- Périmètre : MCP unique + routines systemd sur la VM du homelab ; pas de CLI, pas de container ; agent hors périmètre, intégré plus tard via MCP.
- Publication : idempotente, réconciliée par workout_id, horizon par défaut de 7 jours.
- Routines : sync horaire + publication quotidienne, en timers systemd fournis dans le dépôt, sans installeur interactif.
- Base et données existantes : conservées, migrations additives.
