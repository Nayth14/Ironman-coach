-- PlanState on training plans + extended adaptation_events (ADR-001)

ALTER TABLE training_plans
  ADD COLUMN IF NOT EXISTS plan_state JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE adaptation_events
  ADD COLUMN IF NOT EXISTS proposed_mutations JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS applied_mutations JSONB,
  ADD COLUMN IF NOT EXISTS plan_state_delta JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS playbook_version TEXT,
  ADD COLUMN IF NOT EXISTS pre_checksum TEXT,
  ADD COLUMN IF NOT EXISTS post_checksum TEXT,
  ADD COLUMN IF NOT EXISTS application_status TEXT NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS application_error TEXT,
  ADD COLUMN IF NOT EXISTS diff JSONB;
