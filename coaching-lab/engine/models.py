"""Canonical domain models.

These mirror the schema defined in docs/ADR.md (ADR-005, ADR-008, ADR-014) so
the logic ports cleanly to TypeScript `packages/core` later. Keep field names
and enums aligned with the ADR.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

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


class AdaptationResult(BaseModel):
    decision: AdaptationDecision
    signals: list[str]
    changes: list[str]
    rationale: str


# Pydantic v2 needs this for the self-referencing WorkoutStep.
WorkoutStep.model_rebuild()
