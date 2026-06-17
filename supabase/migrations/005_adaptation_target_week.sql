-- Persist reviewed vs target week on adaptation events

ALTER TABLE adaptation_events
  ADD COLUMN IF NOT EXISTS reviewed_week_number INTEGER,
  ADD COLUMN IF NOT EXISTS target_week_number INTEGER;
