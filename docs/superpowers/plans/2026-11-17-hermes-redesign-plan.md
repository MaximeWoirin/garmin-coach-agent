# Plan d'implémentation : redesign épuré

Date : 2026-11-17. Découle du design 2026-11-06-hermes-redesign-design.md (révision 5).

Principe : chaque jalon tient dans une PR indépendante, testée, qui laisse le repo sain. TDD partout où on touche au comportement (export, réconciliation, scheduler) ; le ménage pur se vérifie par les tests existants.

## Jalon 0 : Ménage OpenClaw

- Supprimer agent/ (identité, skills, playbooks), scripts/install-openclaw-agent.sh, garmin_coach/install_openclaw_agent.py et son exemption de couverture.
- Supprimer les sections OpenClaw du README et des specs qui en parlent (agent.md, scripts.md, export-workflow.md à réécrire au jalon 5).
- Critère de fin : rien dans le repo ne mentionne OpenClaw ; tests verts ; couverture >= 90 sans exemption.

## Jalon 1 : Bibliothèque

- Transformer chaque module script (create_goal, sync_garmin, etc.) en fonctions pures de bibliothèque : l'argparse et l'émission JSON des frontends disparaissent des modules métier ; les fonctions retournent des dicts.
- Créer un unique point de définition des paramètres (types explicites) consommé ensuite par le MCP.
- Adapter les tests : tester les fonctions directement (test_cli et consorts migrent vers des tests de bibliothèque).
- [project.scripts] encore en place à ce stade ; supprimé au jalon 3 avec l'arrivée du MCP.
- Critère de fin : plus aucun frontend argparse ; tests verts ; mypy strict et ruff verts.

## Jalon 2 : Export idempotent et réconciliation

- Monter garminconnect en 0.3.x si nécessaire pour update/delete workout.
- Migration SQL : colonne garmin_workout_id sur les séances planifiées, additive.
- export devient idempotent : publication d'un horizon (par défaut 7 jours), re-pousse d'une séance modifiée (PUT workout), suppression d'une séance retirée du plan (DELETE workout et schedule), jamais de doublon.
- Nouvelle opération adjust (mise à jour ou retrait d'une séance publiée), avec dry_run.
- TDD : un test par cas de réconciliation (nouvelle, modifiée, retirée, inchangée, déjà publiée, dry-run).
- Critère de fin : republication au-dessus d'une semaine déjà publiée = zéro doublon ; séances retirées disparaissent de la montre.

## Jalon 3 : Serveur MCP

- Choisir le framework (fastmcp ou SDK officiel), module garmin_coach/mcp_server.py.
- Outiller les intentions du design (une dizaine d'outils grossiers, un appel = une intention), déléguant aux fonctions du jalon 1, retournant le même JSON.
- Transport streamable HTTP, lié en localhost ; healthcheck.
- Supprimer [project.scripts] ; les usages passent par le MCP.
- TDD : chaque outil testé via un client MCP en process (appel + contrat de retour).
- Critère de fin : tous les usages du design navigables via MCP seul ; tests verts.

## Jalon 4 : Scheduler et container

- Scheduler interne asyncio dans le process du serveur : sync horaire, publication quotidienne le matin (heures configurables par env) ; journalise chaque échec de routine sans tuer le process ; appelle exactement les mêmes fonctions que les outils MCP.
- Dockerfile multi-stage (builder Python 3.13, image finale slim, utilisateur non root), entrypoint unique serveur + scheduler, DB et tokens en volumes, config par env, healthcheck sur l'endpoint MCP.
- Critère de fin : docker run + variables d'environnement suffit pour avoir un container fonctionnel ; comportement identique en dev et en prod.

## Jalon 5 : Déploiement hôte et doc

- deploy/systemd/garmin-coach.service : une seule unité qui lance le container (compose ou docker run), plus rien d'autre côté hôte.
- README remis à plat : conceptualisation du projet (bibliothèque + MCP + container), variables d'environnement, volumes, démarrage.
- Specs mises à jour : agent.md devient le contrat consommateur MCP, scripts.md disparaît au profit de la doc des outils, export-workflow.md réécrit autour de la publication idempotente.
- Critère de fin : une personne qui lit le README sait déployer et consommer ; plus aucune trace du design ancien.

## Après cette itération (hors périmètres actuels)

- Consommation par un agent (Hermes ou autre) via le MCP, exposé par le tunnel du homelab.
- Débrief proactif, planification assistée : décisions agent, pas métier.
