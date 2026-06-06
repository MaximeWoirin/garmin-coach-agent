-- Migration initiale : tables principales

CREATE TABLE training_goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_code TEXT,
  primary_goal TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'medium',
  horizon_date TEXT,
  target_event_name TEXT,
  target_event_date TEXT,
  target_event_priority TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  raw_text TEXT,
  metadata_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (goal_code)
);

CREATE TABLE constraints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_id INTEGER,
  type TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'medium',
  status TEXT NOT NULL DEFAULT 'active',
  scope TEXT NOT NULL DEFAULT 'training',
  start_date TEXT NOT NULL,
  end_date TEXT,
  source TEXT NOT NULL DEFAULT 'user',
  confidence REAL NOT NULL DEFAULT 1.0,
  raw_text TEXT NOT NULL,
  tags_json TEXT,
  notes_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (goal_id) REFERENCES training_goals(id)
);

CREATE TABLE training_blocks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_id INTEGER NOT NULL,
  block_type TEXT NOT NULL,
  week_start TEXT NOT NULL,
  week_end TEXT NOT NULL,
  focus TEXT,
  load_target TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  metadata_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (goal_id) REFERENCES training_goals(id)
);

CREATE TABLE training_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  block_id INTEGER,
  week_start TEXT NOT NULL,
  week_end TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  generated_by TEXT NOT NULL DEFAULT 'agent',
  confidence TEXT NOT NULL DEFAULT 'medium',
  needs_review INTEGER NOT NULL DEFAULT 0,
  metadata_json TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (block_id) REFERENCES training_blocks(id)
);

CREATE TABLE plan_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_id INTEGER NOT NULL,
  planned_date TEXT NOT NULL,
  planned_time TEXT,
  activity_type TEXT NOT NULL,
  duration_min INTEGER NOT NULL,
  intensity TEXT,
  target_hr_low INTEGER,
  target_hr_high INTEGER,
  target_pace_sec_per_km INTEGER,
  target_rpe INTEGER,
  status TEXT NOT NULL DEFAULT 'proposed',
  garmin_event_id TEXT,
  workout_payload_json TEXT,
  tags_json TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES training_plans(id)
);

CREATE TABLE plan_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_id INTEGER NOT NULL,
  reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_by TEXT NOT NULL DEFAULT 'agent',
  reason TEXT NOT NULL,
  summary TEXT,
  suggested_changes_json TEXT,
  outcome TEXT NOT NULL DEFAULT 'kept',
  needs_goal_review INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (plan_id) REFERENCES training_plans(id)
);

CREATE TABLE plan_activity_matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_session_id INTEGER NOT NULL,
  activity_id INTEGER NOT NULL,
  match_type TEXT NOT NULL DEFAULT 'manual',
  confidence REAL NOT NULL DEFAULT 1.0,
  matched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  notes TEXT,
  FOREIGN KEY (plan_session_id) REFERENCES plan_sessions(id),
  FOREIGN KEY (activity_id) REFERENCES activities(id),
  UNIQUE (plan_session_id, activity_id)
);

CREATE TABLE activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL DEFAULT 'garmin',
  external_id TEXT NOT NULL,
  device_id TEXT,
  activity_type TEXT NOT NULL,
  activity_name TEXT,
  start_time_utc TEXT NOT NULL,
  local_start_time TEXT,
  timezone TEXT,
  duration_s INTEGER NOT NULL,
  moving_duration_s INTEGER,
  distance_m REAL,
  elevation_gain_m REAL,
  elevation_loss_m REAL,
  calories_kcal INTEGER,
  avg_hr INTEGER,
  max_hr INTEGER,
  avg_speed_mps REAL,
  max_speed_mps REAL,
  avg_pace_sec_per_km REAL,
  avg_cadence_rpm REAL,
  max_cadence_rpm REAL,
  steps INTEGER,
  avg_power_w REAL,
  max_power_w REAL,
  training_effect_aerobic REAL,
  training_effect_anaerobic REAL,
  perceived_effort INTEGER,
  is_manual INTEGER NOT NULL DEFAULT 0,
  raw_payload_json TEXT,
  imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (source, external_id)
);

CREATE TABLE daily_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL DEFAULT 'garmin',
  metric_date TEXT NOT NULL,
  timezone TEXT,
  steps INTEGER,
  distance_m REAL,
  floors_climbed INTEGER,
  intensity_minutes INTEGER,
  active_calories_kcal INTEGER,
  total_calories_kcal INTEGER,
  resting_hr INTEGER,
  min_hr INTEGER,
  max_hr INTEGER,
  avg_hr INTEGER,
  stress_avg REAL,
  stress_max INTEGER,
  body_battery_start INTEGER,
  body_battery_end INTEGER,
  body_battery_min INTEGER,
  body_battery_max INTEGER,
  respiration_avg REAL,
  pulse_ox_avg REAL,
  raw_payload_json TEXT,
  imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (source, metric_date)
);
