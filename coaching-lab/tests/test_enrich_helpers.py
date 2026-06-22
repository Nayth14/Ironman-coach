"""Tests for deterministic helpers in engine.enrich."""

from __future__ import annotations

from engine.enrich import (
    _duration_valid,
    _has_endurance_structure,
    _normalize_step_type,
    _normalize_target,
    _parse_steps,
    _rpe_for_purpose,
    _sanitize_step_item,
    _step_duration_sum,
    _template_endurance_steps,
    _template_strength_steps,
    template_steps_for_workout,
)
from engine.models import (
    PurposeTag,
    Sport,
    StrengthExercise,
    TargetType,
    Workout,
    WorkoutStatus,
    WorkoutStep,
    WorkoutStepType,
)


# ---------------------------------------------------------------------------
# _rpe_for_purpose
# ---------------------------------------------------------------------------

class TestRpeForPurpose:
    def test_threshold(self):
        t = _rpe_for_purpose(PurposeTag.THRESHOLD)
        assert t.type == TargetType.RPE
        assert t.min == 7 and t.max == 8

    def test_vo2(self):
        t = _rpe_for_purpose(PurposeTag.VO2)
        assert t.min == 7

    def test_race_execution(self):
        t = _rpe_for_purpose(PurposeTag.RACE_EXECUTION)
        assert t.min == 6 and t.max == 7

    def test_aerobic(self):
        t = _rpe_for_purpose(PurposeTag.AEROBIC_BASE)
        assert t.min == 2 and t.max == 4

    def test_recovery(self):
        t = _rpe_for_purpose(PurposeTag.RECOVERY)
        assert t.min == 2 and t.max == 4


# ---------------------------------------------------------------------------
# _step_duration_sum
# ---------------------------------------------------------------------------

class TestStepDurationSum:
    def test_simple_sum(self):
        steps = [
            WorkoutStep(id="1", type=WorkoutStepType.WARMUP, duration_seconds=600),
            WorkoutStep(id="2", type=WorkoutStepType.WORK, duration_seconds=2400),
            WorkoutStep(id="3", type=WorkoutStepType.COOLDOWN, duration_seconds=600),
        ]
        assert _step_duration_sum(steps) == 3600

    def test_repeat_multiplied(self):
        steps = [
            WorkoutStep(id="1", type=WorkoutStepType.REPEAT, duration_seconds=300, repeat_count=4),
        ]
        assert _step_duration_sum(steps) == 1200

    def test_none_durations_ignored(self):
        steps = [
            WorkoutStep(id="1", type=WorkoutStepType.WORK, duration_seconds=None),
            WorkoutStep(id="2", type=WorkoutStepType.WORK, duration_seconds=1000),
        ]
        assert _step_duration_sum(steps) == 1000

    def test_empty(self):
        assert _step_duration_sum([]) == 0


# ---------------------------------------------------------------------------
# _duration_valid
# ---------------------------------------------------------------------------

class TestDurationValid:
    def test_exact_match(self):
        steps = [WorkoutStep(id="1", type=WorkoutStepType.WORK, duration_seconds=3600)]
        assert _duration_valid(steps, 3600) is True

    def test_within_tolerance(self):
        steps = [WorkoutStep(id="1", type=WorkoutStepType.WORK, duration_seconds=3400)]
        assert _duration_valid(steps, 3600) is True  # 3060-4140

    def test_outside_tolerance(self):
        steps = [WorkoutStep(id="1", type=WorkoutStepType.WORK, duration_seconds=2000)]
        assert _duration_valid(steps, 3600) is False

    def test_no_target_checks_non_empty(self):
        steps = [WorkoutStep(id="1", type=WorkoutStepType.WORK)]
        assert _duration_valid(steps, None) is True

    def test_no_target_empty_steps(self):
        assert _duration_valid([], None) is False

    def test_zero_target(self):
        steps = [WorkoutStep(id="1", type=WorkoutStepType.WORK)]
        assert _duration_valid(steps, 0) is True


# ---------------------------------------------------------------------------
# _has_endurance_structure
# ---------------------------------------------------------------------------

class TestHasEnduranceStructure:
    def test_complete_structure(self):
        steps = [
            WorkoutStep(id="1", type=WorkoutStepType.WARMUP),
            WorkoutStep(id="2", type=WorkoutStepType.WORK),
            WorkoutStep(id="3", type=WorkoutStepType.COOLDOWN),
        ]
        assert _has_endurance_structure(steps) is True

    def test_missing_warmup(self):
        steps = [
            WorkoutStep(id="2", type=WorkoutStepType.WORK),
            WorkoutStep(id="3", type=WorkoutStepType.COOLDOWN),
        ]
        assert _has_endurance_structure(steps) is False

    def test_missing_work(self):
        steps = [
            WorkoutStep(id="1", type=WorkoutStepType.WARMUP),
            WorkoutStep(id="3", type=WorkoutStepType.COOLDOWN),
        ]
        assert _has_endurance_structure(steps) is False

    def test_missing_cooldown(self):
        steps = [
            WorkoutStep(id="1", type=WorkoutStepType.WARMUP),
            WorkoutStep(id="2", type=WorkoutStepType.WORK),
        ]
        assert _has_endurance_structure(steps) is False


# ---------------------------------------------------------------------------
# _normalize_step_type
# ---------------------------------------------------------------------------

class TestNormalizeStepType:
    def test_valid_types(self):
        assert _normalize_step_type("warmup") == "warmup"
        assert _normalize_step_type("work") == "work"
        assert _normalize_step_type("cooldown") == "cooldown"
        assert _normalize_step_type("recovery") == "recovery"
        assert _normalize_step_type("rest") == "rest"
        assert _normalize_step_type("repeat") == "repeat"

    def test_aliases(self):
        assert _normalize_step_type("notes") == "work"
        assert _normalize_step_type("note") == "work"
        assert _normalize_step_type("instruction") == "work"
        assert _normalize_step_type("main") == "work"
        assert _normalize_step_type("interval") == "work"
        assert _normalize_step_type("easy") == "recovery"
        assert _normalize_step_type("warm_up") == "warmup"
        assert _normalize_step_type("warm-up") == "warmup"
        assert _normalize_step_type("cool_down") == "cooldown"
        assert _normalize_step_type("cool-down") == "cooldown"
        assert _normalize_step_type("active_recovery") == "recovery"

    def test_unknown_defaults_to_work(self):
        assert _normalize_step_type("nonsense") == "work"

    def test_none_defaults_to_work(self):
        assert _normalize_step_type(None) == "work"

    def test_case_insensitive(self):
        assert _normalize_step_type("WARMUP") == "warmup"
        assert _normalize_step_type("Cooldown") == "cooldown"

    def test_whitespace_stripped(self):
        assert _normalize_step_type("  warmup  ") == "warmup"


# ---------------------------------------------------------------------------
# _normalize_target
# ---------------------------------------------------------------------------

class TestNormalizeTarget:
    def test_valid_target(self):
        result = _normalize_target({"type": "rpe", "min": 5})
        assert result["type"] == "rpe"

    def test_invalid_type_becomes_open(self):
        result = _normalize_target({"type": "invalid_type", "min": 5})
        assert result["type"] == "open"

    def test_none_returns_none(self):
        assert _normalize_target(None) is None

    def test_non_dict_returns_none(self):
        assert _normalize_target("not a dict") is None

    def test_empty_dict_is_falsy(self):
        result = _normalize_target({})
        assert result is None


# ---------------------------------------------------------------------------
# _sanitize_step_item
# ---------------------------------------------------------------------------

class TestSanitizeStepItem:
    def test_notes_type_converted(self):
        item = {"type": "notes", "name": "Fuel reminder", "notes": "Take a gel"}
        result = _sanitize_step_item(item)
        assert result["type"] == "work"
        assert result["notes"] == "Take a gel"

    def test_notes_type_without_notes_field(self):
        item = {"type": "notes", "name": "Do drills"}
        result = _sanitize_step_item(item)
        assert result["type"] == "work"
        assert result["notes"] == "Do drills"
        assert result["name"] == "Do drills"  # name preserved when already set

    def test_notes_type_no_name_no_notes(self):
        item = {"type": "notes", "description": "hydrate"}
        result = _sanitize_step_item(item)
        assert result["type"] == "work"
        assert result["notes"] == "hydrate"
        assert result["name"] == "Coaching note"

    def test_normal_type_preserved(self):
        item = {"type": "warmup", "duration_seconds": 600}
        result = _sanitize_step_item(item)
        assert result["type"] == "warmup"

    def test_target_normalized(self):
        item = {"type": "work", "target": {"type": "weird"}}
        result = _sanitize_step_item(item)
        assert result["target"]["type"] == "open"

    def test_nested_steps_sanitized(self):
        item = {
            "type": "repeat",
            "steps": [
                {"type": "notes", "name": "inner"},
                "not_a_dict",
            ],
        }
        result = _sanitize_step_item(item)
        assert len(result["steps"]) == 1
        assert result["steps"][0]["type"] == "work"


# ---------------------------------------------------------------------------
# _parse_steps
# ---------------------------------------------------------------------------

class TestParseSteps:
    def test_valid_steps(self):
        raw = [
            {"id": "s1", "type": "warmup", "duration_seconds": 600},
            {"id": "s2", "type": "work", "duration_seconds": 2400},
        ]
        steps = _parse_steps(raw)
        assert len(steps) == 2
        assert steps[0].type == WorkoutStepType.WARMUP

    def test_missing_id_generated(self):
        raw = [{"type": "work", "duration_seconds": 1800}]
        steps = _parse_steps(raw)
        assert len(steps) == 1
        assert steps[0].id  # auto-generated

    def test_non_dict_skipped(self):
        raw = ["not a dict", {"id": "s1", "type": "work"}]
        steps = _parse_steps(raw)
        assert len(steps) == 1

    def test_malformed_step_skipped(self):
        raw = [{"id": "s1", "type": "work"}, {"id": "bad", "type": "work", "duration_seconds": "not_int"}]
        steps = _parse_steps(raw)
        assert len(steps) >= 1


# ---------------------------------------------------------------------------
# template_steps_for_workout
# ---------------------------------------------------------------------------

class TestTemplateSteps:
    def test_endurance_workout_has_structure(self):
        w = Workout(
            id="r1", sport=Sport.RUN, title="Easy run",
            purpose_tag=PurposeTag.AEROBIC_BASE,
            estimated_duration_seconds=3600,
            status=WorkoutStatus.PLANNED,
        )
        steps = template_steps_for_workout(w)
        types = {s.type for s in steps}
        assert WorkoutStepType.WARMUP in types
        assert WorkoutStepType.WORK in types
        assert WorkoutStepType.COOLDOWN in types

    def test_strength_with_exercises(self):
        w = Workout(
            id="s1", sport=Sport.STRENGTH, title="Strength",
            purpose_tag=PurposeTag.STRENGTH,
            estimated_duration_seconds=2700,
            exercises=[
                StrengthExercise(name="Squat", sets=3, reps="10"),
                StrengthExercise(name="Plank", sets=3, reps="30s"),
            ],
            status=WorkoutStatus.PLANNED,
        )
        steps = template_steps_for_workout(w)
        assert len(steps) >= 4  # warmup + 2 exercises + cooldown
        assert steps[0].type == WorkoutStepType.WARMUP
        assert steps[-1].type == WorkoutStepType.COOLDOWN
        assert "Squat" in steps[1].name

    def test_strength_without_exercises_falls_back(self):
        w = Workout(
            id="s1", sport=Sport.STRENGTH, title="Strength",
            purpose_tag=PurposeTag.STRENGTH,
            estimated_duration_seconds=1800,
            status=WorkoutStatus.PLANNED,
        )
        steps = template_steps_for_workout(w)
        assert len(steps) >= 3

    def test_duration_sums_correctly(self):
        w = Workout(
            id="b1", sport=Sport.BIKE, title="Long ride",
            purpose_tag=PurposeTag.AEROBIC_BASE,
            estimated_duration_seconds=7200,
            status=WorkoutStatus.PLANNED,
        )
        steps = template_steps_for_workout(w)
        total = sum(s.duration_seconds or 0 for s in steps)
        assert abs(total - 7200) <= 1

    def test_very_short_workout_minimum_durations(self):
        w = Workout(
            id="r1", sport=Sport.RUN, title="Short run",
            purpose_tag=PurposeTag.RECOVERY,
            estimated_duration_seconds=900,
            status=WorkoutStatus.PLANNED,
        )
        steps = template_steps_for_workout(w)
        for s in steps:
            assert (s.duration_seconds or 0) >= 300
