export type Sport = "swim" | "bike" | "run" | "strength" | "brick" | "other";
export type ReadinessVerdict = "green" | "amber" | "red";
export type AdaptationDecision =
  | "progress"
  | "hold"
  | "deload"
  | "bike_substitute"
  | "gut_training";

export interface AthleteProfile {
  goal_type: string;
  race_name: string;
  race_date: string;
  weekly_hours: number;
  limiter_discipline: Sport;
  experience_level: string;
  available_days: number[];
  injury_flags: string[];
  strength_background: string;
  strength_equipment: string;
  current_strength_routine?: string | null;
  strength_restrictions: string[];
  confidence?: string | null;
}

export interface ReadinessResult {
  verdict: ReadinessVerdict;
  weeks_to_race: number;
  rationale: string;
  adjustments: string[];
}

export interface WorkoutStep {
  id: string;
  type: string;
  name?: string | null;
  duration_seconds?: number | null;
  distance_meters?: number | null;
  target?: { type: string; min?: number; max?: number; unit?: string; label?: string } | null;
  notes?: string | null;
  repeat_count?: number | null;
  steps?: WorkoutStep[] | null;
}

export interface Workout {
  id: string;
  sport: Sport;
  title: string;
  description?: string | null;
  scheduled_date?: string | null;
  day_of_week?: number | null;
  purpose_tag: string;
  is_key_session: boolean;
  steps: WorkoutStep[];
  exercises: { name: string; sets: number; reps: string; notes?: string }[];
  estimated_duration_seconds?: number | null;
  estimated_distance_meters?: number | null;
  estimated_tss?: number | null;
  bank_workout_id?: string | null;
  fueling_notes?: string | null;
  status: string;
  week_number?: number;
  phase?: string;
}

export interface Phase {
  name: string;
  start_week: number;
  end_week: number;
  objective: string;
}

export interface PlannedWeek {
  week_number: number;
  phase: string;
  is_deload: boolean;
  target_hours: number;
  strength_plan?: StrengthPlan | null;
  workouts: Workout[];
}

export interface StrengthPlan {
  sessions_per_week: number;
  session_duration_minutes: number;
  focus: string;
  restrictions: string[];
  rationale: string;
}

export interface TrainingPlan {
  athlete_race_date: string;
  total_weeks: number;
  plan_start_date: string;
  phases: Phase[];
  strength_plan: StrengthPlan;
  weeks: PlannedWeek[];
}

export interface PlanGenerateResponse {
  planId: string;
  planStartDate: string;
  profile: AthleteProfile;
  readiness: ReadinessResult;
  plan: TrainingPlan;
  summary: string;
}

export interface WorkoutDiff {
  workout_id: string;
  title: string;
  before_duration_seconds?: number | null;
  after_duration_seconds?: number | null;
  change_summary: string;
}

export interface AdaptationDiff {
  before_hours: number;
  after_hours: number;
  changed_workouts: WorkoutDiff[];
  substitutions: string[];
}

export interface AdaptationEvent {
  eventId?: string;
  id?: string;
  decision: AdaptationDecision;
  signals: string[];
  changes: string[];
  rationale: string;
  mutations?: Record<string, unknown>[];
  planStateDelta?: Record<string, unknown>;
  playbookVersion?: string;
  diff?: AdaptationDiff;
  insufficientData?: boolean;
  reviewedWeekNumber?: number;
  targetWeekNumber?: number;
  applicationStatus?: string;
  user_accepted?: boolean | null;
  weeklyContextSummary?: string | null;
  conformanceStatus?: string | null;
  playbookRuleCited?: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
