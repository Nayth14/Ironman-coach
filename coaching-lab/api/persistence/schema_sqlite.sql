-- SQLite schema mirroring Supabase for local development

CREATE TABLE IF NOT EXISTS athletes (
  id TEXT PRIMARY KEY,
  guest_id TEXT UNIQUE,
  auth_user_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  goal_type TEXT NOT NULL DEFAULT 'finish',
  race_name TEXT,
  race_date TEXT,
  weekly_hours REAL,
  limiter_discipline TEXT,
  experience_level TEXT,
  available_days TEXT DEFAULT '[]',
  injury_flags TEXT DEFAULT '[]',
  strength_background TEXT DEFAULT 'none',
  strength_equipment TEXT DEFAULT 'minimal',
  current_strength_routine TEXT,
  strength_restrictions TEXT DEFAULT '[]',
  confidence TEXT,
  readiness_verdict TEXT,
  readiness_rationale TEXT,
  readiness_adjustments TEXT DEFAULT '[]',
  weeks_to_race INTEGER,
  active_plan_id TEXT
);

CREATE TABLE IF NOT EXISTS training_plans (
  id TEXT PRIMARY KEY,
  athlete_id TEXT NOT NULL,
  race_date TEXT NOT NULL,
  total_weeks INTEGER NOT NULL,
  plan_start_date TEXT,
  status TEXT NOT NULL DEFAULT 'preview',
  strength_plan TEXT NOT NULL DEFAULT '{}',
  summary TEXT,
  created_at TEXT NOT NULL,
  activated_at TEXT
);

CREATE TABLE IF NOT EXISTS phases (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  name TEXT NOT NULL,
  start_week INTEGER NOT NULL,
  end_week INTEGER NOT NULL,
  objective TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workouts (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  athlete_id TEXT NOT NULL,
  week_number INTEGER NOT NULL,
  phase TEXT NOT NULL,
  sport TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  scheduled_date TEXT,
  day_of_week INTEGER,
  purpose_tag TEXT NOT NULL,
  is_key_session INTEGER NOT NULL DEFAULT 0,
  steps TEXT NOT NULL DEFAULT '[]',
  exercises TEXT NOT NULL DEFAULT '[]',
  estimated_duration_seconds INTEGER,
  estimated_distance_meters REAL,
  estimated_tss REAL,
  fueling_notes TEXT,
  status TEXT NOT NULL DEFAULT 'planned',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_completions (
  id TEXT PRIMARY KEY,
  workout_id TEXT NOT NULL,
  athlete_id TEXT NOT NULL,
  completed INTEGER NOT NULL DEFAULT 1,
  rpe INTEGER,
  readiness_score INTEGER,
  fatigue_flags TEXT DEFAULT '[]',
  notes TEXT,
  completed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS adaptation_events (
  id TEXT PRIMARY KEY,
  athlete_id TEXT NOT NULL,
  plan_id TEXT,
  decision TEXT NOT NULL,
  signals TEXT DEFAULT '[]',
  changes TEXT DEFAULT '[]',
  rationale TEXT NOT NULL,
  user_accepted INTEGER,
  triggered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_conversations (
  id TEXT PRIMARY KEY,
  athlete_id TEXT NOT NULL,
  context TEXT NOT NULL DEFAULT 'onboarding',
  messages TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_athletes_guest ON athletes(guest_id);
CREATE INDEX IF NOT EXISTS idx_workouts_athlete ON workouts(athlete_id);
