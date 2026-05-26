# Garmin Coach Agent

Garmin Coach Agent is a local assistant that turns Garmin activity and recovery data into clear training guidance.

The goal is not to replace Garmin or to expose raw database queries to the agent.
The goal is to keep the data layer simple, local, and deterministic, then let the agent reason on top of structured snapshots.

## Why this project exists

Garmin data is useful, but it is usually scattered across app screens, exports, and raw sync artifacts.
This project aims to:

- read local Garmin-related data from SQLite
- compute training and recovery signals in Python
- expose a small internal API made of safe, structured functions
- let an agent produce coaching advice from those functions
- avoid free-form SQL as the main interface

## Core principles

- **Local first**: no cloud dependency for the core logic.
- **Structured over raw**: the agent receives JSON, not arbitrary SQL access.
- **Deterministic helpers**: business logic lives in Python, not in prompt text.
- **Small surface area**: only a few stable commands should be needed.
- **Easy to evolve**: the codebase should start simple, then grow if needed.

## Planned architecture

### 1. SQLite layer

A small Python module opens the database and runs read-only queries.

Example location:

- `garmin_coach/db.py`

Responsibilities:

- connect to SQLite
- fetch activities, sleep, recovery, and summary data
- return Python objects / dicts
- avoid any LLM-specific logic

### 2. Coaching context layer

A service module computes the signals the agent actually needs.

Example location:

- `garmin_coach/context.py`

Possible signals:

- 7-day training load
- recent hard sessions
- sleep trend over 3 days
- days since last hard workout
- fatigue / freshness indicators
- readiness snapshot

### 3. Entry-point scripts

Thin scripts expose a stable interface for the agent and for humans.

Examples:

- `bin/coach-today`
- `bin/coach-week`
- `bin/sync-garmin`

These scripts should output JSON.

### 4. Agent / skill layer

The skill documents how to call the scripts and how to interpret their output.

The agent should:

- call `coach-today` for a daily snapshot
- call `coach-week` for trend analysis
- call `sync-garmin` when fresh data is needed
- never invent raw SQL queries on its own

## MVP spec

### Inputs

The first version only needs local Garmin-related data available in SQLite.

### Outputs

The first version should produce structured coaching context with:

- recent activities
- recent sleep and recovery summary
- load and fatigue indicators
- a concise training recommendation

### Behaviors

- If data is missing, the scripts should say so explicitly.
- If the signal is weak, the agent should say it is uncertain.
- Advice should be short, actionable, and grounded in the computed context.
- The system should prefer simple heuristics over clever inference.

### Non-goals for v0

- no free-form SQL interface for the agent
- no complex UI
- no cloud sync orchestration
- no mobile app
- no multi-user support
- no attempt to model everything Garmin knows

## Suggested repo structure

```text
.
├── README.md
├── garmin_coach/
│   ├── __init__.py
│   ├── db.py
│   └── context.py
├── bin/
│   ├── coach-today
│   ├── coach-week
│   └── sync-garmin
└── tests/
```

## Open questions

- What exact Garmin data source are we syncing from?
- Which metrics are reliable enough for v0?
- Do we want a single `coach` command or separate commands per use case?
- Should the first public interface be CLI only, or CLI plus skill docs?

## Next step

Write the first version of the Python package and the CLI entry points, then freeze the JSON shape before adding more features.
