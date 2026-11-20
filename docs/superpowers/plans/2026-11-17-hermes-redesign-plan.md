# Plan d'implémentation : redesign épuré

Date : 2026-11-17. Révisé le 2026-11-20 après arbitrage d'architecture (révision 6). Découle du design 2026-11-06-hermes-redesign-design.md.

Principe : chaque jalon tient dans une PR indépendante, testée, qui laisse le repo sain. TDD partout où on touche au comportement (export, réconciliation, adaptateurs) ; le ménage pur se vérifie par les tests existants.

Règle transversale : MCP et runner appellent exactement les mêmes fonctions du noyau ; aucune logique métier dans un adaptateur.

## Jalon 0 : Ménage OpenClaw

- Supprimer agent/ (identité, skills, playbooks), scripts/install-openclaw-agent.sh, garmin_coach/install_openclaw_agent.py et son exemption de couverture.
- Supprimer les sections OpenClaw du README et des specs qui en parlent (agent.md, scripts.md, export-workflow.md à réécrire au jalon 5).
- Critère de fin : rien dans le repo ne mentionne OpenClaw ; tests verts ; couverture >= 90 sans exemption.

## Jalon 1 : Noyau bibliothèque

- Transformer chaque module script (create_goal, sync_garmin, etc.) en fonctions pures de bibliothèque : l'argparse et l'émission JSON des frontends disparaissent des modules métier ; les fonctions retournent des dicts.
- Le noyau n'a aucune dépendance de protocole (ni argparse, ni MCP, ni HTTP).
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

## Jalon 3 : Adaptateur MCP

- Choisir le framework (fastmcp ou SDK officiel), composant serveur à part du noyau (import du noyau, aucune logique métier dans l'adaptateur).
- Outiller les intentions du design (une dizaine d'outils grossiers, un appel = une intention), déléguant aux fonctions du noyau, retournant le même JSON.
- Transport streamable HTTP, lié en localhost ; healthcheck.
- Supprimer [project.scripts] ; les usages passent par le MCP (ou le runner au jalon 4).
- TDD : chaque outil testé via un client MCP en process (appel + contrat de retour).
- Critère de fin : tous les usages du design navigables via MCP seul ; tests verts.

## Jalon 4 : Runner interne et container

- Runner minimal : deux commandes (sync, publish) qui appellent les fonctions du noyau ; codes de sortie propres pour systemd ; journalisation verbeuse vers stdout/journald.
- Dockerfile multi-stage (builder Python 3.13, image finale slim, utilisateur non root), une image plusieurs points d'entrée : serve (MCP), sync, publish.
- DB et tokens en volumes ; configuration par variables d'environnement ; healthcheck sur l'endpoint MCP ; SQLite en mode WAL via la chaîne de connexion du noyau.
- TDD : runner testé (les deux commandes délèguent bien aux fonctions du noyau, jamais de logique locale).
- Critère de fin : docker run + variables d'environnement suffit ; sync et publish exécutables en one-shot.

## Jalon 5 : Déploiement systemd et doc

- deploy/systemd/ : garmin-coach.service (lance le container en mode serve), garmin-coach-sync.timer + .service et garmin-coach-publish.timer + .service (docker run --rm one-shot du runner). Installation documentée en quelques commandes explicites, aucun installeur interactif.
- README remis à plat : les trois composants (noyau, MCP, runner), variables d'environnement, volumes, démarrage.
- Specs mises à jour : agent.md devient le contrat consommateur MCP, scripts.md disparaît au profit de la doc du runner et des outils, export-workflow.md réécrit autour de la publication idempotente.
- Critère de fin : une personne qui lit le README sait déployer et consommer ; plus aucune trace du design ancien.

## Après cette itération (hors périmètres actuels)

- Consommation par un agent (Hermes ou autre) via le MCP, exposé par le tunnel du homelab.
- Débrief proactif, planification assistée : décisions agent, pas métier.
