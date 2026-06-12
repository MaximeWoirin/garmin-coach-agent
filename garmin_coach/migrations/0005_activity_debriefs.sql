CREATE TABLE activity_debriefs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  activity_id INTEGER NOT NULL,
  plan_session_id INTEGER,
  status TEXT NOT NULL DEFAULT 'pending',
  prompt_count INTEGER NOT NULL DEFAULT 0,
  first_prompted_at TEXT,
  last_prompted_at TEXT,
  completed_at TEXT,
  dismissed_at TEXT,
  rpe INTEGER,
  pain_during INTEGER,
  pain_after INTEGER,
  pain_next_morning INTEGER,
  note TEXT,
  source TEXT NOT NULL DEFAULT 'agent',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
  FOREIGN KEY (plan_session_id) REFERENCES plan_sessions(id) ON DELETE SET NULL,
  UNIQUE (activity_id),
  CHECK (status IN ('pending', 'prompted', 'completed', 'dismissed')),
  CHECK (rpe IS NULL OR (rpe >= 1 AND rpe <= 10)),
  CHECK (pain_during IS NULL OR (pain_during >= 0 AND pain_during <= 10)),
  CHECK (pain_after IS NULL OR (pain_after >= 0 AND pain_after <= 10)),
  CHECK (pain_next_morning IS NULL OR (pain_next_morning >= 0 AND pain_next_morning <= 10))
);

CREATE INDEX idx_activity_debriefs_status
  ON activity_debriefs(status);

CREATE INDEX idx_activity_debriefs_plan_session
  ON activity_debriefs(plan_session_id);
