-- Add plan_start_date for calendar-anchored workouts
ALTER TABLE training_plans ADD COLUMN IF NOT EXISTS plan_start_date DATE;
