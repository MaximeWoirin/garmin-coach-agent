# Redesign Hermes : Garmin Coach Agent

Date : 2026-11-06. Issue de l'atelier de recadrage (Maxime + Vibe).

## Intention et pourquoi

Le projet a grandi autour d'OpenClaw : script d'installation à trois modes, 17 skills miroirs, timers systemd, crons de livraison Telegram. Ce runtime est aujourd'hui totalement coupé et le packaging qu'il exigeait constitue l'essentiel de la complexité du dépôt.

Le besoin recadré est simple : un coach qui planifie les séances d'entraînement, les publie sur la montre Garmin, suit ce qui a réellement été fait, et tient compte du contexte de vie (contraintes, objectifs, forme, douleurs).

Le nouvel hôte est Hermes Agent (Nous Research), auto-hébergé dans le homelab. Il fournit nativement tout ce que le packaging OpenClaw simulait à la main : cron, livraison Telegram, mémoire persistante, skills, MCP.

## Objectifs

- Planification hebdomadaire autonome : le dimanche, le coach planifie la semaine et publie les séances sur Garmin sans validation humaine préalable, puis envoie un récap Telegram.
- Débrief après chaque séance : la sync détecte une nouvelle activité, le coach envoie un débrief proactif (regroupé si plusieurs activités), avec suivi systématique des douleurs et gênes.
- Ajustements en cours de semaine, y compris de dernière minute : modifier ou retirer une séance déjà publiée sur Garmin.
- Contexte de vie : les données structurées (contraintes, objectifs, plans, débriefs résumés) vivent dans la base SQLite existante ; le ressenti, les douleurs et les notes subjectives vivent dans la mémoire d'Hermes.

## Non-objectifs

- Pas de multi-utilisateur.
- Pas de refonte de la couche métier Python (sync, export, SQLite, scripts) tant qu'elle fait le job.
- Pas d'interface web.
- Pas d'utilisation depuis Vibe dans cette itération.

## Anti-objectifs

- Réintroduire un packaging d'agent lourd : pas de script d'installation interactif, pas de venv managé, pas de gestion de timers systemd dans le dépôt. Le piège OpenClaw ne doit pas se reproduire.
- Exposer des micro-outils à l'agent : un outil MCP = une intention.

## Contraintes

- Python >= 3.13, SQLite, migrations SQL existantes.
- garminconnect (montée de 0.2.x vers 0.3.x si nécessaire pour update/delete workout).
- L'authentification Garmin et les tokens restent côté homelab (auth.py inchangé dans son principe).
- Hermes est le seul consommateur de la couche métier ; le MCP est le point d'entrée standard.

## Approches considérées

1. Hermes hôte unique + MCP fin sur le noyau Python existant (retenue). Hermes remplace point par point le packaging mort : cron natif, Telegram, mémoire, skills. Aligné avec la stratégie homelab (même pattern que Email Zero : le service expose un MCP, l'agent consomme).
2. Vibe hôte unique (écartée) : aucun runtime disponible chez Vibe pour la sync horaire, le rafraîchissement du token Garmin ou l'export vers la montre.
3. Hybride Hermes worker + Vibe consommateur du MCP (écartée) : deux surfaces à maintenir pour un usage perso ; le débrief post-séance arrive naturellement sur Telegram de toute façon.

## Conception retenue

### Ce qui reste

- Le package garmin_coach : scripts CLI, DB, migrations, sync, plans, contraintes, objectifs, débriefs.
- Les tests et la grille qualité (couverture >= 90, mypy strict, ruff).

### Ce qui est ajouté

- Un serveur MCP fin (FastMCP ou SDK officiel, au choix du builder), module garmin_coach/mcp_server.py, exposant une dizaine d'outils grossiers, un appel = une intention. Chaque outil délègue à la fonction métier existante et retourne le même JSON que les scripts CLI :
  - sync_garmin, get_fitness_state, get_activities, get_current_plan
  - create_plan_draft, create_plan_session, delete_plan_session, set_plan_session_status, set_plan_status
  - get_constraints, create_constraint, set_constraint_status
  - get_goals, create_goal
  - get_pending_debriefs, save_activity_debrief, mark_activity_debrief_prompted
  - export_plan_garmin (avec dry_run), adjust_plan_garmin (mise à jour ou retrait d'une séance déjà publiée)
- Deux ou trois playbooks Hermes (planification hebdo, débrief proactif) : fichiers markdown courts dans un dossier hermes/ du dépôt, à recopier dans le workspace Hermes par l'utilisateur.

### Ce qui est supprimé

- Le répertoire agent/ complet (identité, skills, playbooks OpenClaw).
- scripts/install-openclaw-agent.sh et garmin_coach/install_openclaw_agent.py.
- Toutes les sections OpenClaw du README et des specs concernées.

### Évolutions de la couche export (le seul vrai travail métier)

- Publication de la semaine entière au moment du plan (le design ancien était borné à demain avec export quotidien ; il disparaît au profit d'un export au moment du plan, puis réexport difficiel après ajustement).
- Ajustements : mise à jour (PUT workout) et suppression (DELETE workout et schedule) via workout-service ; montée garminconnect en 0.3.x si nécessaire.
- Persistance des identifiants de workout Garmin (nouvelle colonne en base) pour permettre la réconciliation lors des ajustements.
- Le mapping sports locaux vers workout-service reste valable (docs/spec/garmin-workout-sport-mapping.md).

### Contrat d'usage de l'agent (remplace docs/spec/agent.md)

- L'agent n'émet pas de SQL libre ; il appelle les outils MCP.
- Heuristiques simples, réponses courtes, signalement de l'incertitude quand le signal est faible.
- Suivi systématique des douleurs et gênes lors des débriefs.

### Automatisations Hermes (configuration Hermes, pas dans le dépôt)

- Dimanche soir : planification, publication autonome, récap Telegram.
- Toutes les heures : sync ; si nouvelles activités, débrief regroupé.
- À la demande : ajustements de plan en cours de semaine.

## Resté au builder

- Choix du framework MCP et nommage exact des outils.
- Structure du module serveur MCP et gestion des sessions DB.
- Migration export pour update/delete (avec tests) et colonne workout_id.
- Nettoyage de la doc : README, docs/spec/agent.md, export-workflow.md.
- Découpage en jalons / PRs.

## Décisions de l'atelier

- Hôte : Hermes hôte unique (option A).
- Publication : autonome au moment du plan, sans validation humaine préalable.
- Ajustements : possibles à tout moment, y compris dernière minute.
- Débrief : après chaque séance, regroupé si plusieurs activités.
- Vibe : hors du périmètre de cette itération.
