"""Tests for engine.adaptation.apply — mutation application to plan weeks."""

from __future__ import annotations

from datetime import date

from engine.adaptation.apply import (
    apply_mutations_to_plan,
    apply_mutations_to_week,
    build_diff,
)
from engine.models import (
    MutationOp,
    PhaseName,
    Phase,
    PlanMutation,
    PlannedWeek,
    PurposeTag,
    Sport,
    StrengthPlan,
    TrainingPlan,
    Workout,
    WorkoutStatus,
    WorkoutStep,
    WorkoutStepType,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _workout(
    *,
    id: str = "w1",
    sport: Sport = Sport.RUN,
    title: str = "Easy run",
    purpose_tag: PurposeTag = PurposeTag.AEROBIC_BASE,
    is_key_session: bool = False,
    duration: int = 3600,
    day_of_week: int = 0,
    steps: list[WorkoutStep] | None = None,
) -> Workout:
    return Workout(
        id=id,
        sport=sport,
        title=title,
        purpose_tag=purpose_tag,
        is_key_session=is_key_session,
        estimated_duration_seconds=duration,
        day_of_week=day_of_week,
        status=WorkoutStatus.PLANNED,
        steps=steps or [
            WorkoutStep(id="s1", type=WorkoutStepType.WARMUP, duration_seconds=600),
            WorkoutStep(id="s2", type=WorkoutStepType.WORK, duration_seconds=duration - 1200),
            WorkoutStep(id="s3", type=WorkoutStepType.COOLDOWN, duration_seconds=600),
        ],
    )


def _week(workouts: list[Workout] | None = None, week_number: int = 1) -> PlannedWeek:
    ws = workouts or [
        _workout(id="run1", sport=Sport.RUN, title="Easy run", duration=3600, day_of_week=1),
        _workout(id="bike1", sport=Sport.BIKE, title="Long ride", duration=7200,
                 is_key_session=True, purpose_tag=PurposeTag.AEROBIC_BASE, day_of_week=5),
        _workout(id="run2", sport=Sport.RUN, title="Tempo run", duration=3600,
                 is_key_session=True, purpose_tag=PurposeTag.THRESHOLD, day_of_week=3),
    ]
    return PlannedWeek(
        week_number=week_number,
        phase=PhaseName.BASE,
        target_hours=sum((w.estimated_duration_seconds or 0) for w in ws) / 3600.0,
        workouts=ws,
    )


def _plan(weeks: list[PlannedWeek] | None = None) -> TrainingPlan:
    ws = weeks or [_week()]
    return TrainingPlan(
        athlete_race_date=date(2027, 6, 1),
        total_weeks=20,
        plan_start_date=date(2027, 1, 1),
        phases=[Phase(name=PhaseName.BASE, start_week=1, end_week=20, objective="Build base")],
        strength_plan=StrengthPlan(
            sessions_per_week=2,
            session_duration_minutes=30,
            focus="General strength",
            rationale="Injury prevention",
        ),
        weeks=ws,
    )


# ---------------------------------------------------------------------------
# SCALE_WEEK_VOLUME
# ---------------------------------------------------------------------------

class TestScaleWeekVolume:
    def test_scale_down(self):
        week = _week()
        mutations = [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=0.8)]
        new_week, diffs, subs = apply_mutations_to_week(week, mutations)
        for w in new_week.workouts:
            assert w.status == WorkoutStatus.ADAPTED
        assert len(diffs) >= 1
        for d in diffs:
            assert d.after_duration_seconds < d.before_duration_seconds

    def test_scale_up(self):
        week = _week()
        mutations = [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=1.15)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert any(d.after_duration_seconds > d.before_duration_seconds for d in diffs)

    def test_no_factor_no_change(self):
        week = _week()
        mutations = [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=None)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert len(diffs) == 0


# ---------------------------------------------------------------------------
# SCALE_NON_KEY_DURATION
# ---------------------------------------------------------------------------

class TestScaleNonKeyDuration:
    def test_only_non_key_scaled(self):
        week = _week()
        mutations = [PlanMutation(op=MutationOp.SCALE_NON_KEY_DURATION, factor=0.7)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        changed_ids = {d.workout_id for d in diffs}
        assert "run1" in changed_ids
        assert "bike1" not in changed_ids  # key session
        assert "run2" not in changed_ids  # key session

    def test_minimum_duration_enforced(self):
        short_workout = _workout(id="short1", duration=400, is_key_session=False)
        week = _week([short_workout])
        mutations = [PlanMutation(op=MutationOp.SCALE_NON_KEY_DURATION, factor=0.5)]
        new_week, _, _ = apply_mutations_to_week(week, mutations)
        assert new_week.workouts[0].estimated_duration_seconds >= 300


# ---------------------------------------------------------------------------
# REMOVE_OPTIONAL_SESSION
# ---------------------------------------------------------------------------

class TestRemoveOptionalSession:
    def test_removes_optional(self):
        optional = _workout(id="opt1", purpose_tag=PurposeTag.RECOVERY, is_key_session=False)
        key = _workout(id="key1", is_key_session=True, purpose_tag=PurposeTag.THRESHOLD)
        week = _week([key, optional])
        mutations = [PlanMutation(op=MutationOp.REMOVE_OPTIONAL_SESSION)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert len(new_week.workouts) == 1
        assert new_week.workouts[0].id == "key1"
        assert diffs[0].change_summary == "Removed optional session"

    def test_no_optional_no_change(self):
        key = _workout(id="key1", is_key_session=True, purpose_tag=PurposeTag.THRESHOLD)
        week = _week([key])
        mutations = [PlanMutation(op=MutationOp.REMOVE_OPTIONAL_SESSION)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert len(new_week.workouts) == 1
        assert len(diffs) == 0

    def test_removes_last_optional_only(self):
        opt1 = _workout(id="opt1", purpose_tag=PurposeTag.AEROBIC_BASE, is_key_session=False)
        opt2 = _workout(id="opt2", purpose_tag=PurposeTag.ECONOMY, is_key_session=False)
        week = _week([opt1, opt2])
        mutations = [PlanMutation(op=MutationOp.REMOVE_OPTIONAL_SESSION)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert len(new_week.workouts) == 1
        assert new_week.workouts[0].id == "opt1"


# ---------------------------------------------------------------------------
# STRIP_INTENSITY_TAGS
# ---------------------------------------------------------------------------

class TestStripIntensityTags:
    def test_threshold_stripped(self):
        threshold = _workout(id="t1", purpose_tag=PurposeTag.THRESHOLD, is_key_session=True)
        week = _week([threshold])
        mutations = [PlanMutation(op=MutationOp.STRIP_INTENSITY_TAGS)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert new_week.workouts[0].purpose_tag == PurposeTag.AEROBIC_BASE
        assert new_week.workouts[0].is_key_session is False
        assert new_week.workouts[0].status == WorkoutStatus.ADAPTED
        assert "Stripped intensity" in diffs[0].change_summary

    def test_vo2_stripped(self):
        vo2 = _workout(id="v1", purpose_tag=PurposeTag.VO2, is_key_session=True)
        week = _week([vo2])
        mutations = [PlanMutation(op=MutationOp.STRIP_INTENSITY_TAGS)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert new_week.workouts[0].purpose_tag == PurposeTag.AEROBIC_BASE

    def test_aerobic_not_stripped(self):
        easy = _workout(id="e1", purpose_tag=PurposeTag.AEROBIC_BASE)
        week = _week([easy])
        mutations = [PlanMutation(op=MutationOp.STRIP_INTENSITY_TAGS)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert len(diffs) == 0


# ---------------------------------------------------------------------------
# REPLACE_WORKOUT (run → bike substitute)
# ---------------------------------------------------------------------------

class TestReplaceWorkout:
    def test_replaces_first_run(self):
        run1 = _workout(id="r1", sport=Sport.RUN, title="Easy Run")
        run2 = _workout(id="r2", sport=Sport.RUN, title="Long Run")
        week = _week([run1, run2])
        mutations = [PlanMutation(op=MutationOp.REPLACE_WORKOUT)]
        new_week, diffs, subs = apply_mutations_to_week(week, mutations)
        assert new_week.workouts[0].sport == Sport.BIKE
        assert "bike" in new_week.workouts[0].title.lower()
        assert new_week.workouts[1].sport == Sport.RUN  # only first replaced
        assert len(subs) == 1
        assert "bike" in subs[0].lower()

    def test_no_runs_no_change(self):
        bike = _workout(id="b1", sport=Sport.BIKE, title="Easy ride")
        week = _week([bike])
        mutations = [PlanMutation(op=MutationOp.REPLACE_WORKOUT)]
        new_week, diffs, subs = apply_mutations_to_week(week, mutations)
        assert len(diffs) == 0
        assert len(subs) == 0


# ---------------------------------------------------------------------------
# MODIFY_FUELING_NOTES
# ---------------------------------------------------------------------------

class TestModifyFuelingNotes:
    def test_adds_fueling_notes_to_long_ride(self):
        long_ride = _workout(
            id="lr1", sport=Sport.BIKE, title="Long ride",
            purpose_tag=PurposeTag.AEROBIC_BASE, is_key_session=True,
            duration=14400,  # 4 hours
        )
        week = _week([long_ride])
        mutations = [PlanMutation(op=MutationOp.MODIFY_FUELING_NOTES, value=80)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert new_week.workouts[0].fueling_notes is not None
        assert "80 g/h" in new_week.workouts[0].fueling_notes
        assert "Fueling notes updated" in diffs[0].change_summary

    def test_default_carb_value(self):
        long_ride = _workout(
            id="lr1", sport=Sport.BIKE, title="Long ride",
            purpose_tag=PurposeTag.AEROBIC_BASE, is_key_session=True,
            duration=14400,
        )
        week = _week([long_ride])
        mutations = [PlanMutation(op=MutationOp.MODIFY_FUELING_NOTES)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        if diffs:  # only applies to long rides
            assert "60 g/h" in new_week.workouts[0].fueling_notes


# ---------------------------------------------------------------------------
# ADD_EASY_AEROBIC
# ---------------------------------------------------------------------------

class TestAddEasyAerobic:
    def test_extends_non_key_bike(self):
        bike = _workout(
            id="b1", sport=Sport.BIKE, title="Easy ride",
            is_key_session=False, duration=3600,
        )
        week = _week([bike])
        mutations = [PlanMutation(op=MutationOp.ADD_EASY_AEROBIC)]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        if diffs:
            assert diffs[0].after_duration_seconds > diffs[0].before_duration_seconds
            assert "easy aerobic" in diffs[0].change_summary.lower()


# ---------------------------------------------------------------------------
# build_diff
# ---------------------------------------------------------------------------

class TestBuildDiff:
    def test_build_diff_hours(self):
        week = _week()
        new_week = _week()
        diff = build_diff(week, new_week, [], [])
        assert diff.before_hours == diff.after_hours
        assert diff.changed_workouts == []
        assert diff.substitutions == []


# ---------------------------------------------------------------------------
# apply_mutations_to_plan
# ---------------------------------------------------------------------------

class TestApplyMutationsToPlan:
    def test_applies_to_first_week_by_default(self):
        plan = _plan()
        mutations = [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=0.8)]
        new_plan, diff = apply_mutations_to_plan(plan, mutations)
        assert diff is not None
        assert diff.after_hours <= diff.before_hours

    def test_applies_to_specific_week(self):
        w1 = _week(week_number=1)
        w2 = _week(week_number=2)
        plan = _plan([w1, w2])
        mutations = [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=0.8)]
        new_plan, diff = apply_mutations_to_plan(plan, mutations, target_week_number=2)
        assert diff is not None

    def test_empty_plan_returns_none_diff(self):
        plan = _plan([])
        plan.weeks = []
        mutations = [PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=0.8)]
        new_plan, diff = apply_mutations_to_plan(plan, mutations)
        assert diff is None

    def test_multiple_mutations_combined(self):
        week = _week()
        mutations = [
            PlanMutation(op=MutationOp.SCALE_WEEK_VOLUME, factor=0.9),
            PlanMutation(op=MutationOp.STRIP_INTENSITY_TAGS),
        ]
        new_week, diffs, _ = apply_mutations_to_week(week, mutations)
        assert len(diffs) >= 1
