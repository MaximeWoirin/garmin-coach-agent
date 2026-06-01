-- Ajout de la table sync_runs

CREATE TABLE sync_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL DEFAULT 'garmin',
  sync_type TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  range_start TEXT,
  range_end TEXT,
  activities_seen INTEGER NOT NULL DEFAULT 0,
  activities_inserted INTEGER NOT NULL DEFAULT 0,
  activities_updated INTEGER NOT NULL DEFAULT 0,
  daily_metrics_seen INTEGER NOT NULL DEFAULT 0,
  daily_metrics_upserted INTEGER NOT NULL DEFAULT 0,
  cursor_value TEXT,
  error_message TEXT
);
