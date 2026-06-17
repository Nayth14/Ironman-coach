-- Weekly check-in context for NL adaptation input

CREATE TABLE IF NOT EXISTS weekly_checkins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  athlete_id UUID NOT NULL REFERENCES athletes(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES training_plans(id) ON DELETE SET NULL,
  week_number INTEGER,
  conversation_id UUID REFERENCES chat_conversations(id) ON DELETE SET NULL,
  extracted_context JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_weekly_checkins_athlete ON weekly_checkins(athlete_id);

ALTER TABLE adaptation_events
  ADD COLUMN IF NOT EXISTS weekly_checkin_id UUID REFERENCES weekly_checkins(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS canonical_decision TEXT,
  ADD COLUMN IF NOT EXISTS llm_proposed_decision TEXT,
  ADD COLUMN IF NOT EXISTS conformance_status TEXT,
  ADD COLUMN IF NOT EXISTS playbook_rule_cited TEXT,
  ADD COLUMN IF NOT EXISTS weekly_context_summary TEXT;
