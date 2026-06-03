# Agent

Ce dossier contient la documentation de travail de l’agent coach.

But :
- séparer la logique LLM de la logique métier Python
- documenter le rôle, le ton, les outils, et les séquences d’usage
- garder une base simple à itérer sans toucher au code métier à chaque ajustement de prompt

## Structure

- `AGENTS.md` — règles de vie de l’agent dans son workspace
- `BOOTSTRAP.md` — point d’entrée du premier démarrage
- `IDENTITY.md` — identité de base de l’agent
- `HEARTBEAT.md` — tâches périodiques légères si le runtime en utilise
- `SYSTEM.md` — rôle, règles, limites, contrat de réponse
- `SOUL.md` — ton, style, posture conversationnelle
- `TOOLS.md` — quels scripts appeler, dans quel ordre, pour quelle mission
- `skills/` — skills métier alignés avec les scripts publics
- `playbooks/` — séquences d’orchestration par cas d’usage

## Ce qui ne doit pas vivre ici

Pas de mémoire runtime volatile.

Exemples à garder hors Git :
- historique de conversation brut
- traces d’exécution
- derniers snapshots temporaires
- brouillons de réponse
- caches Garmin ou LLM

Cette donnée peut vivre plus tard dans un dossier comme `data/agent/` ou `state/agent/`, ignoré par Git.

## Principe

Le code Python du projet reste la source de vérité pour :
- la donnée
- les transformations déterministes
- les contrats JSON

L’agent, lui, doit :
- consommer ces sorties structurées
- décider quel outil appeler ensuite
- produire un conseil clair, prudent, et actionnable
