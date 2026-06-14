-- Ironman Coach — initial schema
-- Anonymous-first identity (ADR-006); canonical workout model (ADR-005)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------------
-- Athletes
-- ---------------------------------------------------------------------------

CREATE TABLE athletes (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  guest_id              UUID UNIQUE,
  auth_user_id          UUID REFERENCES auth.users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Profile fields (from AthleteProfile)
  goal_type             TEXT NOT NULL DEFAULT 'finish',
  race_name             TEXT,
  race_date             DATE,
  weekly_hours          DOUBLE PRECISION,
  limiter_discipline    TEXT,
  experience_level      TEXT,
  available_days        INTEGER[] DEFAULT '{}',
  injury_flags          TEXT[] DEFAULT '{}',
  strength_background   TEXT DEFAULT 'none',
  strength_equipment    TEXT DEFAULT 'minimal',
  current_strength_routine TEXT,
  strength_restrictions TEXT[] DEFAULT '{}',
  confidence            TEXT,

  -- Readiness snapshot
  readiness_verdict     TEXT,
  readiness_rationale   TEXT,
  readiness_adjustments TEXT[] DEFAULT '{}',
  weeks_to_race         INTEGER,

  -- Active plan reference
  active_plan_id        UUID
);

CREATE INDEX idx_athletes_guest_id ON athletes(guest_id);
CREATE INDEX idx_athletes_auth_user_id ON athletes(auth_user_id);

-- ---------------------------------------------------------------------------
-- Training plans
-- ---------------------------------------------------------------------------

CREATE TABLE training_plans (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  athlete_id        UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  race_date         DATE NOT NULL,
  total_weeks       INTEGER NOT NULL,
  status            TEXT NOT NULL DEFAULT 'preview',  -- preview | active | archived
  strength_plan     JSONB NOT NULL DEFAULT '{}',
  summary           TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  activated_at      TIMESTAMPTZ
);

CREATE INDEX idx_training_plans_athlete ON training_plans(athlete_id);
CREATE INDEX idx_training_plans_status ON training_plans(athlete_id, status);

ALTER TABLE athletes
  ADD CONSTRAINT fk_athletes_active_plan
  FOREIGN KEY (active_plan_id) REFERENCES training_plans(id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- Phases
-- ---------------------------------------------------------------------------

CREATE TABLE phases (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id       UUID NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  start_week    INTEGER NOT NULL,
  end_week      INTEGER NOT NULL,
  objective     TEXT NOT NULL
);

CREATE INDEX idx_phases_plan ON phases(plan_id);

-- ---------------------------------------------------------------------------
-- Workouts
-- ---------------------------------------------------------------------------

CREATE TABLE workouts (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id                     UUID NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
  athlete_id                  UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  week_number                 INTEGER NOT NULL,
  phase                       TEXT NOT NULL,
  sport                       TEXT NOT NULL,
  title                       TEXT NOT NULL,
  description                 TEXT,
  scheduled_date              DATE,
  day_of_week                 INTEGER,
  purpose_tag                 TEXT NOT NULL,
  is_key_session              BOOLEAN NOT NULL DEFAULT false,
  steps                       JSONB NOT NULL DEFAULT '[]',
  exercises                   JSONB NOT NULL DEFAULT '[]',
  estimated_duration_seconds  INTEGER,
  estimated_distance_meters   DOUBLE PRECISION,
  estimated_tss               DOUBLE PRECISION,
  fueling_notes               TEXT,
  status                      TEXT NOT NULL DEFAULT 'planned',
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workouts_plan ON workouts(plan_id);
CREATE INDEX idx_workouts_athlete ON workouts(athlete_id);
CREATE INDEX idx_workouts_sport ON workouts(athlete_id, sport);
CREATE INDEX idx_workouts_status ON workouts(athlete_id, status);
CREATE INDEX idx_workouts_scheduled ON workouts(athlete_id, scheduled_date);

-- ---------------------------------------------------------------------------
-- Workout completions
-- ---------------------------------------------------------------------------

CREATE TABLE workout_completions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workout_id      UUID NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
  athlete_id      UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  completed       BOOLEAN NOT NULL DEFAULT true,
  rpe             INTEGER CHECK (rpe >= 1 AND rpe <= 10),
  readiness_score INTEGER CHECK (readiness_score >= 1 AND readiness_score <= 10),
  fatigue_flags   TEXT[] DEFAULT '{}',
  notes           TEXT,
  completed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_completions_workout ON workout_completions(workout_id);
CREATE INDEX idx_completions_athlete ON workout_completions(athlete_id);

-- ---------------------------------------------------------------------------
-- Adaptation events
-- ---------------------------------------------------------------------------

CREATE TABLE adaptation_events (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  athlete_id      UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  plan_id         UUID REFERENCES training_plans(id) ON DELETE SET NULL,
  decision        TEXT NOT NULL,
  signals         TEXT[] DEFAULT '{}',
  changes         TEXT[] DEFAULT '{}',
  rationale       TEXT NOT NULL,
  user_accepted   BOOLEAN,
  triggered_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_adaptations_athlete ON adaptation_events(athlete_id);

-- ---------------------------------------------------------------------------
-- Chat conversations
-- ---------------------------------------------------------------------------

CREATE TABLE chat_conversations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  athlete_id  UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  context     TEXT NOT NULL DEFAULT 'onboarding',  -- onboarding | coaching
  messages    JSONB NOT NULL DEFAULT '[]',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_athlete ON chat_conversations(athlete_id, context);

-- ---------------------------------------------------------------------------
-- Updated-at trigger
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER athletes_updated_at
  BEFORE UPDATE ON athletes
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER chat_updated_at
  BEFORE UPDATE ON chat_conversations
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security (enabled; API uses service role in MVP)
-- ---------------------------------------------------------------------------

ALTER TABLE athletes ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE phases ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_completions ENABLE ROW LEVEL SECURITY;
ALTER TABLE adaptation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS. Future auth policies:
CREATE POLICY athletes_guest_select ON athletes
  FOR SELECT USING (guest_id::text = current_setting('request.headers', true)::json->>'x-guest-id');

CREATE POLICY athletes_service_all ON athletes
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY plans_service_all ON training_plans
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY phases_service_all ON phases
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY workouts_service_all ON workouts
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY completions_service_all ON workout_completions
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY adaptations_service_all ON adaptation_events
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY chat_service_all ON chat_conversations
  FOR ALL USING (auth.role() = 'service_role');
