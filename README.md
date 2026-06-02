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

## Statut

- code applicatif : base V0 implémentée
- tests : présents avec couverture minimale
- prochaine étape : itérer sur l’orchestration agent et ses playbooks
