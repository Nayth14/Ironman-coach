"""Pydantic models for the parsed Adaptation Playbook."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class GuardrailsSpec(BaseModel):
    max_weekly_increase: float = 0.10
    max_deload_reduction: float = 0.50
    default_deload_factor: float = 0.35
    min_deload_factor: float = 0.30
    easy_intensity_min_fraction: float = 0.80
    easy_mandatory_weekly_hours: float = 15.0
    easy_recommended_weekly_hours: float = 7.0


class WindowsSpec(BaseModel):
    decision_days: int = 7
    trend_days: int = 14
    macro_days: int = 28


class ThresholdsSpec(BaseModel):
    high_rpe: int = 8
    low_readiness: int = 4
    high_rpe_min_sessions: int = 2
    low_readiness_min_sessions: int = 2
    deload_flag_count: int = 3
    hold_flag_count_min: int = 1
    min_completed_sessions: int = 3
    min_key_completed_sessions: int = 1
    partial_week_min_sessions: int = 5
    consecutive_holds_escalate: int = 2
    consecutive_deloads_freeze_weeks: int = 2
    per050_recovery_days_min: int = 3
    per050_recovery_days_max: int = 5
    illness_days_off_threshold: int = 3


class FlagWeightsSpec(BaseModel):
    missed_key_session: float = 2.0
    missed_optional_session: float = 0.5
    missed_default_session: float = 1.0


class PriorityRankSpec(BaseModel):
    rank: int
    name: str
    hold_trim_max: Optional[float] = None
    deload_trim_max: Optional[float] = None
    hold_trim_first: bool = False
    hold_remove_first: bool = False
    deload_remove: bool = False
    deload_strip_intensity: bool = False
    hold_drop_second_session: bool = False
    deload_strip_heavy: bool = False


class DecisionEntrySpec(BaseModel):
    all_completed: Optional[bool] = None
    all_rpe_below_high: Optional[bool] = None
    zero_warning_flags: Optional[bool] = None
    min_completed_sessions: Optional[int] = None
    min_key_completed: Optional[int] = None
    require_14_day_clean: Optional[bool] = None
    injury_flags_disable: Optional[bool] = None
    flag_count_min: Optional[int] = None
    flag_count_max: Optional[int] = None
    consecutive_holds_escalate: Optional[int] = None
    sport: Optional[str] = None
    orthopedic_keywords_match: Optional[bool] = None
    gi_keywords_match: Optional[bool] = None


class DecisionPlaybookSpec(BaseModel):
    entry: DecisionEntrySpec = Field(default_factory=DecisionEntrySpec)
    mutations: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)


class GutTrainingSpec(BaseModel):
    carb_floor_default: int = 60
    carb_ramp_per_week: int = 5
    systemic_session_threshold: int = 2


class RunVolumeCapSpec(BaseModel):
    beginner: float = 0.6
    intermediate: float = 0.7
    advanced: float = 0.8
    niggle_cap: Optional[float] = None
    chronic_weeks_persist: int = 2
    lift_increment_per_week: float = 0.1


class MacroRulesSpec(BaseModel):
    hold_progression_drop: int = 1
    clean_week_progression_recover: int = 1
    consecutive_holds_pull_deload: int = 1
    base_extension_hold_threshold: int = 3
    base_extension_deload_threshold: int = 2
    amber_weeks_cap_peak: int = 3
    phase_shift_max_weeks: int = 1


class GoldenScenarioSpec(BaseModel):
    id: str
    name: str
    phase: str = "base"
    week_number: int = 1
    experience: str = "intermediate"
    completions: list[dict[str, Any]] = Field(default_factory=list)
    prior_week_clean: bool = True
    plan_state: dict[str, Any] = Field(default_factory=dict)
    is_deload_week: bool = False
    illness_days_off: int = 0
    expected_decision: str
    expected_mutations: list[str] = Field(default_factory=list)
    insufficient_data: bool = False
    must_not: list[str] = Field(default_factory=list)


class PlaybookSpec(BaseModel):
    version: str = "1.0"
    guardrails: GuardrailsSpec = Field(default_factory=GuardrailsSpec)
    windows: WindowsSpec = Field(default_factory=WindowsSpec)
    thresholds: ThresholdsSpec = Field(default_factory=ThresholdsSpec)
    flag_weights: FlagWeightsSpec = Field(default_factory=FlagWeightsSpec)
    orthopedic_keywords: list[str] = Field(default_factory=list)
    gi_keywords: list[str] = Field(default_factory=list)
    chronic_orthopedic_min_sessions: int = 2
    chronic_orthopedic_window_days: int = 14
    experience_progress_caps: dict[str, float] = Field(default_factory=dict)
    phase_progress_factors: dict[str, float] = Field(default_factory=dict)
    experience_hold_trim: dict[str, float] = Field(default_factory=dict)
    hold_trim_single_flag: float = 0.10
    hold_trim_multi_flag: float = 0.20
    run_volume_cap: RunVolumeCapSpec = Field(default_factory=RunVolumeCapSpec)
    gut_training: GutTrainingSpec = Field(default_factory=GutTrainingSpec)
    priority_ranks: list[PriorityRankSpec] = Field(default_factory=list)
    decisions: dict[str, DecisionPlaybookSpec] = Field(default_factory=dict)
    macro_rules: MacroRulesSpec = Field(default_factory=MacroRulesSpec)
    narrator_templates: dict[str, str] = Field(default_factory=dict)
    golden_scenarios: list[GoldenScenarioSpec] = Field(default_factory=list)
