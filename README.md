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

Le fichier shell est maintenant un bootstrap fin :
- `scripts/install-openclaw-agent.sh` résout Python puis délègue
- la logique d'installation vit dans `python -m garmin_coach.install_openclaw_agent`

Par défaut, le script devient interactif :
- il lit `~/.openclaw/openclaw.json`
- il détecte les agents déjà configurés
- il propose d’installer sur `main` ou sur un agent existant
- si l’agent cible a une allowlist de skills, il propose d’y ajouter les skills Garmin

Le même script sert pour les trois cas :
- `install` sur une cible vierge
- `update` sur une installation saine déjà présente
- `repair` quand l’état détecté est partiel ou incohérent

Par défaut il auto-détecte le mode. On peut aussi passer `--mode install|update|repair` comme garde-fou explicite.

Le script :
- copie les fichiers `agent/*` dans le workspace de l’agent cible
- copie les playbooks dans `playbooks/` si le dossier existe dans le repo
- copie les skills dans `skills/`
- crée un runtime Python managé dans `<workspace>/.garmin-coach-agent/.venv`
- installe un timer `systemd --user` pour la sync Garmin automatique (par défaut `OnCalendar=hourly`)
- installe un timer `systemd --user` pour exporter chaque jour vers Garmin les séances prévues demain
- peut créer / mettre à jour un cron OpenClaw de weekly planning si un `session-key` ou une delivery explicite est fourni(e)
- peut créer / mettre à jour un cron OpenClaw de débrief proactif post-séance si un `session-key` ou une delivery explicite est fourni(e)
- peut créer / mettre à jour un cron OpenClaw hebdomadaire de ménage des contraintes si un `session-key` ou une delivery explicite est fourni(e)
- réécrit les commandes des skills pour pointer vers ce runtime
- sauvegarde les fichiers remplacés dans `.garmin-coach-agent/backups/<timestamp>/`
- sauvegarde aussi la config OpenClaw avant patch si une allowlist doit être modifiée

Options utiles :

```bash
./scripts/install-openclaw-agent.sh --dry-run
./scripts/install-openclaw-agent.sh --agent main
./scripts/install-openclaw-agent.sh --mode update --agent main
./scripts/install-openclaw-agent.sh --sync-on-calendar '*-*-* 06:00:00'
./scripts/install-openclaw-agent.sh --export-on-calendar '*-*-* 07:00:00'
./scripts/install-openclaw-agent.sh --weekly-planning-session-key 'agent:garmin-coach:telegram:direct:8771763758'
./scripts/install-openclaw-agent.sh --weekly-planning-to 'telegram:8771763758' --weekly-planning-channel telegram --weekly-planning-account garmin_clawch_bot
./scripts/install-openclaw-agent.sh --activity-debrief-session-key 'agent:garmin-coach:telegram:direct:8771763758'
./scripts/install-openclaw-agent.sh --activity-debrief-to 'telegram:8771763758' --activity-debrief-channel telegram --activity-debrief-account garmin_clawch_bot
./scripts/install-openclaw-agent.sh --constraint-cleanup-session-key 'agent:garmin-coach:telegram:direct:8771763758'
./scripts/install-openclaw-agent.sh --constraint-cleanup-to 'telegram:8771763758' --constraint-cleanup-channel telegram --constraint-cleanup-account garmin_clawch_bot
./scripts/install-openclaw-agent.sh --skip-systemd-sync
./scripts/install-openclaw-agent.sh --skip-systemd-export
./scripts/install-openclaw-agent.sh --skip-weekly-planning-cron
./scripts/install-openclaw-agent.sh --skip-activity-debrief-cron
./scripts/install-openclaw-agent.sh --skip-constraint-cleanup-cron
./scripts/install-openclaw-agent.sh --workspace /chemin/vers/workspace
./scripts/install-openclaw-agent.sh --no-bootstrap
```

Notes produit :

- le weekly planning reste une feature du produit, mais il demande un vrai contexte cible ; l'installeur le crée seulement s'il sait où poster / dans quelle session tourner
- le débrief proactif post-séance s'appuie sur `playbooks/proactive_activity_debrief.md`, groupe plusieurs activités en un seul message et insiste sur le suivi des douleurs / gênes pour les blessures
- le ménage hebdomadaire des contraintes s'appuie sur `playbooks/constraint_cleanup.md` et sur le script structuré `get-constraint-cleanup`
- le timer systemd d'export Garmin reste borné à **demain** ; il n'est pas utilisé pour publier toute une semaine d'un coup

## Statut

- code applicatif : base V0 implémentée
- tests : présents avec couverture minimale
- prochaine étape : itérer sur l’orchestration agent et ses playbooks
