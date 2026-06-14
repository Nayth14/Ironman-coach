/**
 * Supabase / database types for Ironman Coach.
 * Regenerate from schema when migrations change.
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface AthleteRow {
  id: string;
  guest_id: string | null;
  auth_user_id: string | null;
  created_at: string;
  updated_at: string;
  goal_type: string;
  race_name: string | null;
  race_date: string | null;
  weekly_hours: number | null;
  limiter_discipline: string | null;
  experience_level: string | null;
  available_days: number[];
  injury_flags: string[];
  strength_background: string;
  strength_equipment: string;
  current_strength_routine: string | null;
  strength_restrictions: string[];
  confidence: string | null;
  readiness_verdict: string | null;
  readiness_rationale: string | null;
  readiness_adjustments: string[];
  weeks_to_race: number | null;
  active_plan_id: string | null;
}

export interface TrainingPlanRow {
  id: string;
  athlete_id: string;
  race_date: string;
  total_weeks: number;
  plan_start_date: string | null;
  status: "preview" | "active" | "archived";
  strength_plan: Json;
  summary: string | null;
  created_at: string;
  activated_at: string | null;
}

export interface PhaseRow {
  id: string;
  plan_id: string;
  name: string;
  start_week: number;
  end_week: number;
  objective: string;
}

export interface WorkoutRow {
  id: string;
  plan_id: string;
  athlete_id: string;
  week_number: number;
  phase: string;
  sport: string;
  title: string;
  description: string | null;
  scheduled_date: string | null;
  day_of_week: number | null;
  purpose_tag: string;
  is_key_session: boolean;
  steps: Json;
  exercises: Json;
  estimated_duration_seconds: number | null;
  estimated_distance_meters: number | null;
  estimated_tss: number | null;
  fueling_notes: string | null;
  status: string;
  created_at: string;
}

export interface WorkoutCompletionRow {
  id: string;
  workout_id: string;
  athlete_id: string;
  completed: boolean;
  rpe: number | null;
  readiness_score: number | null;
  fatigue_flags: string[];
  notes: string | null;
  completed_at: string;
}

export interface AdaptationEventRow {
  id: string;
  athlete_id: string;
  plan_id: string | null;
  decision: string;
  signals: string[];
  changes: string[];
  rationale: string;
  user_accepted: boolean | null;
  triggered_at: string;
}

export interface ChatConversationRow {
  id: string;
  athlete_id: string;
  context: "onboarding" | "coaching";
  messages: Json;
  created_at: string;
  updated_at: string;
}
