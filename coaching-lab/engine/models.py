"""Canonical domain models.

These mirror the schema defined in docs/ADR.md (ADR-005, ADR-008, ADR-014) so
the logic ports cleanly to TypeScript `packages/core` later. Keep field names
and enums aligned with the ADR.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Sport(str, Enum):
    SWIM = "swim"
    BIKE = "bike"
    RUN = "run"
    STRENGTH = "strength"
    BRICK = "brick"
    OTHER = "other"


class GoalType(str, Enum):
    FINISH = "finish"
    PR = "pr"
    RETURN = "return"


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StrengthBackground(str, Enum):
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"


class StrengthEquipment(str, Enum):
    GYM = "gym"
    HOME = "home"
    MINIMAL = "minimal"


class PhaseName(str, Enum):
    PREP = "prep"
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"


class PurposeTag(str, Enum):
    AEROBIC_BASE = "aerobic_base"
    DURABILITY = "durability"
    THRESHOLD = "threshold"
    VO2 = "vo2"
    ECONOMY = "economy"
    FUELING = "fueling"
    RACE_EXECUTION = "race_execution"
    RECOVERY = "recovery"
    STRENGTH = "strength"


class WorkoutStepType(str, Enum):
    WARMUP = "warmup"
    WORK = "work"
    RECOVERY = "recovery"
    REST = "rest"
    COOLDOWN = "cooldown"
    REPEAT = "repeat"


class TargetType(str, Enum):
    PACE = "pace"
    POWER = "power"
    HEART_RATE = "heart_rate"
    RPE = "rpe"
    CADENCE = "cadence"
    OPEN = "open"


class WorkoutStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ADAPTED = "adapted"


class ReadinessVerdict(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class AdaptationDecision(str, Enum):
    PROGRESS = "progress"
    HOLD = "hold"
    DELOAD = "deload"
    BIKE_SUBSTITUTE = "bike_substitute"
    GUT_TRAINING = "gut_training"


class ConformanceStatus(str, Enum):
    MATCHED = "matched"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ProgressionRate(str, Enum):
    FROZEN = "frozen"
    SLOW = "slow"
    NORMAL = "normal"


class MutationOp(str, Enum):
    SCALE_WEEK_VOLUME = "scale_week_volume"
    SCALE_NON_KEY_DURATION = "scale_non_key_duration"
    REMOVE_OPTIONAL_SESSION = "remove_optional_session"
    REPLACE_WORKOUT = "replace_workout"
    STRIP_INTENSITY_TAGS = "strip_intensity_tags"
    FORCE_DELOAD_WEEK = "force_deload_week"
    INSERT_RECOVERY_BLOCK = "insert_recovery_block"
    MODIFY_FUELING_NOTES = "modify_fueling_notes"
    FREEZE_PROGRESSION_RATE = "freeze_progression_rate"
    PULL_DELOAD_FORWARD = "pull_deload_forward"
    SET_RUN_VOLUME_CAP = "set_run_volume_cap"
    SET_GUT_TRAINING_MODE = "set_gut_training_mode"
    ADD_EASY_AEROBIC = "add_easy_aerobic"
    ADVANCE_PROGRESSION_RATE = "advance_progression_rate"
    HOLD_GLOBAL_VOLUME = "hold_global_volume"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    REJECTED = "rejected"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Athlete profile (extracted from onboarding chat)
# ---------------------------------------------------------------------------


class AthleteProfile(BaseModel):
    """Structured output of the onboarding conversation.

    The LLM extracts this from the chat; deterministic rules act on it.
    """

    goal_type: GoalType
    race_name: str
    race_date: date
    weekly_hours: float = Field(ge=3, le=30)
    limiter_discipline: Sport
    experience_level: ExperienceLevel
    available_days: list[int] = Field(
        description="Days of week available, 0=Mon..6=Sun"
    )

    # Injury / safety
    injury_flags: list[str] = Field(default_factory=list)

    # Strength (ADR-014)
    strength_background: StrengthBackground = StrengthBackground.NONE
    strength_equipment: StrengthEquipment = StrengthEquipment.MINIMAL
    current_strength_routine: Optional[str] = None
    strength_restrictions: list[str] = Field(default_factory=list)

    # Optional
    confidence: Optional[str] = None


# ---------------------------------------------------------------------------
# Workouts
# ---------------------------------------------------------------------------


class WorkoutTarget(BaseModel):
    type: TargetType
    min: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None
    label: Optional[str] = None


class WorkoutStep(BaseModel):
    id: str
    type: WorkoutStepType
    name: Optional[str] = None
    duration_seconds: Optional[int] = None
    distance_meters: Optional[float] = None
    target: Optional[WorkoutTarget] = None
    notes: Optional[str] = None
    repeat_count: Optional[int] = None
    steps: Optional[list["WorkoutStep"]] = None


class StrengthExercise(BaseModel):
    name: str
    sets: int
    reps: str  # e.g. "8-12" or "30s"
    notes: Optional[str] = None
    restriction_safe: bool = True


class Workout(BaseModel):
    id: str
    sport: Sport
    title: str
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    day_of_week: Optional[int] = None  # 0=Mon..6=Sun, for template weeks
    purpose_tag: PurposeTag
    is_key_session: bool = False
    steps: list[WorkoutStep] = Field(default_factory=list)
    exercises: list[StrengthExercise] = Field(default_factory=list)
    estimated_duration_seconds: Optional[int] = None
    estimated_distance_meters: Optional[float] = None
    estimated_tss: Optional[float] = None
    fueling_notes: Optional[str] = None
    status: WorkoutStatus = WorkoutStatus.PLANNED


# ---------------------------------------------------------------------------
# Plan structure
# ---------------------------------------------------------------------------


class Phase(BaseModel):
    name: PhaseName
    start_week: int
    end_week: int
    objective: str


class StrengthPlan(BaseModel):
    sessions_per_week: int
    session_duration_minutes: int
    focus: str
    restrictions: list[str] = Field(default_factory=list)
    rationale: str


class PlannedWeek(BaseModel):
    week_number: int
    phase: PhaseName
    is_deload: bool = False
    target_hours: float
    strength_plan: Optional[StrengthPlan] = None
    workouts: list[Workout] = Field(default_factory=list)


class TrainingPlan(BaseModel):
    athlete_race_date: date
    total_weeks: int
    plan_start_date: date
    phases: list[Phase]
    strength_plan: StrengthPlan
    weeks: list[PlannedWeek] = Field(default_factory=list)


class ReadinessResult(BaseModel):
    verdict: ReadinessVerdict
    weeks_to_race: int
    rationale: str
    adjustments: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Feedback + adaptation
# ---------------------------------------------------------------------------


class WorkoutCompletion(BaseModel):
    workout_id: str
    sport: Sport
    completed: bool
    rpe: Optional[int] = Field(default=None, ge=1, le=10)
    readiness_score: Optional[int] = Field(default=None, ge=1, le=10)
    fatigue_flags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    is_key_session: bool = False
    is_optional: bool = False
    week_number: Optional[int] = None
    completed_at: Optional[date] = None


class PlanState(BaseModel):
    """Mutable trajectory state for an active training plan."""

    volume_multiplier: float = 1.0
    progression_rate: ProgressionRate = ProgressionRate.NORMAL
    forced_deload_weeks: list[int] = Field(default_factory=list)
    run_volume_cap: float = 1.0
    gut_training_mode: bool = False
    gut_carb_floor: Optional[int] = None
    consecutive_holds: int = 0
    consecutive_deloads: int = 0
    weeks_since_recovery: int = 0
    progression_frozen_weeks: int = 0
    decision_history: list[str] = Field(default_factory=list)
    illness_reentry: bool = False


class PlanMutation(BaseModel):
    """Machine-readable mutation operation."""

    op: MutationOp
    factor: Optional[float] = None
    weeks: Optional[int] = None
    days: Optional[int] = None
    workout_id: Optional[str] = None
    target_sport: Optional[Sport] = None
    value: Optional[float] = None
    bool_value: Optional[bool] = None
    notes: Optional[str] = None


class WorkoutDiff(BaseModel):
    workout_id: str
    title: str
    before_duration_seconds: Optional[int] = None
    after_duration_seconds: Optional[int] = None
    change_summary: str


class AdaptationDiff(BaseModel):
    before_hours: float
    after_hours: float
    changed_workouts: list[WorkoutDiff] = Field(default_factory=list)
    substitutions: list[str] = Field(default_factory=list)


class WeeklyContext(BaseModel):
    week_number: int | None = None
    summary: str = ""
    fatigue_flags: list[str] = Field(default_factory=list)
    illness_days_off: int = 0
    life_stress: bool = False
    missed_key_reason: str | None = None
    athlete_quotes: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"


class LlmAdaptationProposal(BaseModel):
    decision: AdaptationDecision
    rationale: str
    signal_augmentations: WeeklyContext
    playbook_rule_cited: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"


class AdaptationResult(BaseModel):
    decision: AdaptationDecision
    signals: list[str]
    changes: list[str]
    rationale: str
    mutations: list[PlanMutation] = Field(default_factory=list)
    plan_state_delta: dict[str, object] = Field(default_factory=dict)
    playbook_version: Optional[str] = None
    diff: Optional[AdaptationDiff] = None
    insufficient_data: bool = False
    reviewed_week_number: Optional[int] = None
    target_week_number: Optional[int] = None
    weekly_context_summary: Optional[str] = None
    conformance_status: Optional[ConformanceStatus] = None
    playbook_rule_cited: Optional[str] = None
    canonical_decision: Optional[AdaptationDecision] = None
    llm_proposed_decision: Optional[AdaptationDecision] = None


# Pydantic v2 needs this for the self-referencing WorkoutStep.
WorkoutStep.model_rebuild()
