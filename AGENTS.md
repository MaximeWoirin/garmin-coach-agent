# Garmin Coach Agent — AI Agent Instructions

## Project Status

**Pre-code phase.** The specs are the source of truth for V0. Do not start implementing before reading the relevant spec.

- [docs/README.md](docs/README.md) — documentation index
- [docs/spec/README.md](docs/spec/README.md) — objectives and macro view
- [docs/spec/architecture.md](docs/spec/architecture.md) — architecture
- [docs/spec/code.md](docs/spec/code.md) — Python code architecture and module layout
- [docs/spec/database.md](docs/spec/database.md) — SQLite schema
- [docs/spec/scripts.md](docs/spec/scripts.md) — scripts and CLI
- [docs/spec/agent.md](docs/spec/agent.md) — agent contract and constraints
- [docs/spec/tools/](docs/spec/tools/) — the four functional tool blocks

## Tech Stack

- **Language:** Python (module pattern: `python -m garmin_coach.<script-name>`)
- **Database:** SQLite (local, file-based)
- **Data exchange:** JSON snapshots between scripts and agent

## Architecture

```
Garmin API → sync-garmin → SQLite → scripts → JSON snapshot → agent → advice
```

Five components: **Tools**, **Scripts**, **Cron**, **Database**, **Agent**.

**Critical constraint:** The agent never queries SQLite directly. It calls scripts, which produce JSON snapshots. Scripts are the only interface to the database.

## Scripts

All scripts follow this pattern:

```bash
python -m garmin_coach.<script-name> [--options]
```

Authentication is part of the project contract too:

```bash
python -m garmin_coach.auth_garmin [--options]
```

Common flags: `--dry-run`, `--week-start`/`--week-end`, `--start`/`--end`, `--limit`, `--plan-id`, `--session-id`, `--goal-id`.

**Output contract** — every script returns:

```json
{
  "status": "success | partial | failed",
  "warnings": [],
  "errors": []
}
```

Plus domain-specific fields. Scripts must be **idempotent** and output **stable JSON structure**.

## Functional Tool Blocks

| Block | Scripts | Status |
|-------|---------|--------|
| Activities | `sync-garmin`, `get-activities` | Partial |
| Metrics | `sync-garmin`, `get-fitness-state` | Complete for V0 |
| Constraints | `get-constraints`, `create-constraint`, `delete-constraint`, `set-constraint-status` | Tooling specified |
| Plans | `get-current-plan`, `create-plan-draft`, `create-plan-session`, `set-plan-status`, `set-plan-session-status`, `delete-plan-session`, `export-plan-garmin` | Tooling specified |

## Plan & Session State Machines

**Plan:** `draft → active → sent → archived`
**Session:** `draft → proposed → exported → done | skipped | canceled`

Status changes may cascade (e.g. plan `draft → active` cascades sessions to `proposed`). All transitions must be idempotent.

## Agent Constraints

The agent must:
- Call scripts from the relevant business block per task
- Consume JSON snapshots from those scripts
- Call `sync-garmin` if data needs refreshing
- Signal uncertainty when data is missing or signal is weak

The agent must **not**:
- Run free SQL queries
- Invent or over-interpret metrics not produced by a script
- Write long responses when one sentence suffices

## Database

See [docs/spec/database.md](docs/spec/database.md) for the full schema. Key tables: `training_goals`, `constraints`, `training_blocks`, `training_plans`, `plan_sessions`, `activities`, `daily_metrics`, `plan_activity_matches`.

- Use ISO dates (`YYYY-MM-DD`). Preserve raw Garmin payloads where possible.
- Stable personal context (goals, preferences) lives in **agent memory**, not the DB.
