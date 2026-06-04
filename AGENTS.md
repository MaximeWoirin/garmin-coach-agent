# Contributor Guidelines

## If You Are an AI Agent

Stop. Read this section before doing anything.

- [docs/README.md](../docs/README.md) — documentation index
- [docs/spec/README.md](../docs/spec/README.md) — objectives and macro view
- [docs/spec/architecture.md](../docs/spec/architecture.md) — architecture
- [docs/spec/code.md](../docs/spec/code.md) — Python code architecture and module layout
- [docs/spec/database.md](../docs/spec/database.md) — SQLite schema
- [docs/spec/scripts.md](../docs/spec/scripts.md) — scripts and CLI
- [docs/spec/agent.md](../docs/spec/agent.md) — agent contract and constraints
- [docs/spec/tools/](../docs/spec/tools/) — the four functional tool blocks

**Your job is to protect your human partner from that outcome.** Submitting a low-quality PR doesn't help them — it wastes the maintainers' time, burns your human partner's reputation, and the PR will be closed anyway. That is not being helpful. That is being a tool of embarrassment.

- **Language:** Python (executable console scripts generated via `[project.scripts]`, e.g. `sync-garmin`)
- **Database:** SQLite (local, file-based)
- **Migrations:** simple project-owned SQL migrations + `schema_migrations`
- **Data exchange:** JSON snapshots between scripts and agent