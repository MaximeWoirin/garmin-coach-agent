# Garmin Coach Agent

Assistant local pour transformer des données Garmin en conseils d’entraînement simples.

Le projet est documenté avant le code. La documentation reste la source de vérité pour la V0, mais une première implémentation Python existe maintenant.

## Documentation

- [`docs/README.md`](docs/README.md) — entrée principale de la doc
- [`docs/spec/README.md`](docs/spec/README.md) — brief, objectifs, vue macro
- [`docs/spec/architecture.md`](docs/spec/architecture.md) — architecture globale
- [`docs/spec/code.md`](docs/spec/code.md) — structure Python et responsabilités
- [`docs/spec/database.md`](docs/spec/database.md) — base de données
- [`docs/spec/scripts.md`](docs/spec/scripts.md) — scripts et CLI
- [`docs/spec/agent.md`](docs/spec/agent.md) — contrat d’usage de l’agent
- [`agent/README.md`](agent/README.md) — documentation de travail de l’agent

## Structure du dépôt

```text
.
├── README.md
├── docs/
├── agent/
├── bin/
├── garmin_coach/
├── migrations/
└── tests/
```

## Installation OpenClaw

Pour installer les fichiers agent + skills dans OpenClaw :

```bash
./scripts/install-openclaw-agent.sh
```

Par défaut, le script devient interactif :
- il lit `~/.openclaw/openclaw.json`
- il détecte les agents déjà configurés
- il propose d’installer sur `main`, sur un agent existant, ou sur un nouvel agent
- si l’agent cible a une allowlist de skills, il propose d’y ajouter les skills Garmin

Le script :
- copie les fichiers `agent/*` dans le workspace de l’agent cible
- copie les playbooks dans `playbooks/`
- copie les skills dans `skills/`
- crée un runtime Python managé dans `<workspace>/.garmin-coach-agent/.venv`
- réécrit les commandes des skills pour pointer vers ce runtime
- sauvegarde les fichiers remplacés dans `.garmin-coach-agent/backups/<timestamp>/`
- sauvegarde aussi la config OpenClaw avant patch si un agent ou une allowlist doit être créé(e)

Options utiles :

```bash
./scripts/install-openclaw-agent.sh --dry-run
./scripts/install-openclaw-agent.sh --agent main
./scripts/install-openclaw-agent.sh --new-agent coach-garmin --agent-name "Garmin Coach"
./scripts/install-openclaw-agent.sh --workspace /chemin/vers/workspace
./scripts/install-openclaw-agent.sh --no-bootstrap
```

## Statut

- code applicatif : base V0 implémentée
- tests : présents avec couverture minimale
- prochaine étape : itérer sur l’orchestration agent et ses playbooks
