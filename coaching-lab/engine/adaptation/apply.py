"""Apply mutations to materialized plan weeks."""

from __future__ import annotations

import copy

from engine.models import (
    AdaptationDiff,
    MutationOp,
    PhaseName,
    PlanMutation,
    PlannedWeek,
    PurposeTag,
    Sport,
    TrainingPlan,
    Workout,
    WorkoutDiff,
    WorkoutStatus,
)
from engine.rules import semantics as sem


def _week_hours(week: PlannedWeek) -> float:
    total_sec = sum(sem.duration_seconds(w) for w in week.workouts if w.sport != Sport.STRENGTH)
    return total_sec / 3600.0


def _scale_duration(workout: Workout, factor: float) -> Workout:
    w = workout.model_copy(deep=True)
    if w.estimated_duration_seconds:
        w.estimated_duration_seconds = max(300, int(w.estimated_duration_seconds * factor))
    for step in w.steps:
        if step.duration_seconds:
            step.duration_seconds = max(60, int(step.duration_seconds * factor))
    w.status = WorkoutStatus.ADAPTED
    return w


def _is_optional(w: Workout) -> bool:
    return not w.is_key_session and w.purpose_tag in (
        PurposeTag.AEROBIC_BASE,
        PurposeTag.ECONOMY,
        PurposeTag.RECOVERY,
    )


def _strip_intensity(w: Workout) -> Workout:
    out = w.model_copy(deep=True)
    if out.purpose_tag in (PurposeTag.THRESHOLD, PurposeTag.VO2, PurposeTag.RACE_EXECUTION):
        out.purpose_tag = PurposeTag.AEROBIC_BASE
        out.is_key_session = False
    out.status = WorkoutStatus.ADAPTED
    return out


def _replace_run_with_bike(w: Workout) -> Workout:
    out = w.model_copy(deep=True)
    out.sport = Sport.BIKE
    out.title = out.title.replace("Run", "Bike").replace("run", "bike")
    if "Run" in out.title or "run" in out.title:
        out.title = "Easy bike (run substitute)"
    else:
        out.title = f"{out.title} → easy bike substitute"
    out.purpose_tag = PurposeTag.AEROBIC_BASE
    out.is_key_session = False
    out.status = WorkoutStatus.ADAPTED
    return out


def apply_mutations_to_week(
    week: PlannedWeek,
    mutations: list[PlanMutation],
    *,
    phase: PhaseName = PhaseName.BASE,
) -> tuple[PlannedWeek, list[WorkoutDiff], list[str]]:
    """Apply mutations to a single week; return updated week + diffs."""
    before_hours = _week_hours(week)
    workouts = [copy.deepcopy(w) for w in week.workouts]
    diffs: list[WorkoutDiff] = []
    subs: list[str] = []

    for mutation in mutations:
        if mutation.op == MutationOp.SCALE_WEEK_VOLUME and mutation.factor:
            for i, w in enumerate(workouts):
                before = w.estimated_duration_seconds
                workouts[i] = _scale_duration(w, mutation.factor)
                if before != workouts[i].estimated_duration_seconds:
                    diffs.append(
                        WorkoutDiff(
                            workout_id=w.id,
                            title=w.title,
                            before_duration_seconds=before,
                            after_duration_seconds=workouts[i].estimated_duration_seconds,
                            change_summary=f"Scaled volume ×{mutation.factor:.2f}",
                        )
                    )

        elif mutation.op == MutationOp.SCALE_NON_KEY_DURATION and mutation.factor:
            for i, w in enumerate(workouts):
                if w.is_key_session:
                    continue
                before = w.estimated_duration_seconds
                workouts[i] = _scale_duration(w, mutation.factor)
                if before != workouts[i].estimated_duration_seconds:
                    diffs.append(
                        WorkoutDiff(
                            workout_id=w.id,
                            title=w.title,
                            before_duration_seconds=before,
                            after_duration_seconds=workouts[i].estimated_duration_seconds,
                            change_summary=f"Trimmed non-key ×{mutation.factor:.2f}",
                        )
                    )

        elif mutation.op == MutationOp.REMOVE_OPTIONAL_SESSION:
            optional_idxs = [i for i, w in enumerate(workouts) if _is_optional(w)]
            if optional_idxs:
                idx = optional_idxs[-1]
                removed = workouts.pop(idx)
                diffs.append(
                    WorkoutDiff(
                        workout_id=removed.id,
                        title=removed.title,
                        change_summary="Removed optional session",
                    )
                )

        elif mutation.op == MutationOp.STRIP_INTENSITY_TAGS:
            for i, w in enumerate(workouts):
                if w.purpose_tag in (PurposeTag.THRESHOLD, PurposeTag.VO2):
                    before_tag = w.purpose_tag.value
                    workouts[i] = _strip_intensity(w)
                    diffs.append(
                        WorkoutDiff(
                            workout_id=w.id,
                            title=w.title,
                            change_summary=f"Stripped intensity ({before_tag} → aerobic)",
                        )
                    )

        elif mutation.op == MutationOp.REPLACE_WORKOUT:
            for i, w in enumerate(workouts):
                if w.sport == Sport.RUN:
                    before_title = w.title
                    workouts[i] = _replace_run_with_bike(w)
                    subs.append(f"{before_title} → easy bike substitute")
                    diffs.append(
                        WorkoutDiff(
                            workout_id=w.id,
                            title=workouts[i].title,
                            change_summary="Replaced run with bike endurance",
                        )
                    )
                    break

        elif mutation.op == MutationOp.MODIFY_FUELING_NOTES:
            for i, w in enumerate(workouts):
                if w.sport in (Sport.BIKE, Sport.BRICK) and sem.is_long_ride(w):
                    carb = int(mutation.value or 60)
                    workouts[i] = w.model_copy(deep=True)
                    workouts[i].fueling_notes = (
                        f"Gut training: start {carb} g/h carbs; one drink mix; ramp +5 g/h weekly."
                    )
                    workouts[i].status = WorkoutStatus.ADAPTED
                    diffs.append(
                        WorkoutDiff(
                            workout_id=w.id,
                            title=w.title,
                            change_summary=f"Fueling notes updated ({carb} g/h floor)",
                        )
                    )

        elif mutation.op == MutationOp.ADD_EASY_AEROBIC:
            for i, w in enumerate(workouts):
                if not w.is_key_session and w.sport == Sport.BIKE:
                    before = w.estimated_duration_seconds
                    workouts[i] = _scale_duration(w, 1.08)
                    if before != workouts[i].estimated_duration_seconds:
                        diffs.append(
                            WorkoutDiff(
                                workout_id=w.id,
                                title=w.title,
                                before_duration_seconds=before,
                                after_duration_seconds=workouts[i].estimated_duration_seconds,
                                change_summary="Added easy aerobic volume",
                            )
                        )
                    break

    new_week = week.model_copy(deep=True)
    new_week.workouts = workouts
    new_week.target_hours = _week_hours(new_week)
    after_hours = new_week.target_hours

    return new_week, diffs, subs


def build_diff(week: PlannedWeek, new_week: PlannedWeek, diffs: list[WorkoutDiff], subs: list[str]) -> AdaptationDiff:
    return AdaptationDiff(
        before_hours=_week_hours(week),
        after_hours=_week_hours(new_week),
        changed_workouts=diffs,
        substitutions=subs,
    )


def apply_mutations_to_plan(
    plan: TrainingPlan,
    mutations: list[PlanMutation],
    target_week_number: int | None = None,
) -> tuple[TrainingPlan, AdaptationDiff | None]:
    if not plan.weeks:
        return plan, None
    week_num = target_week_number or plan.weeks[0].week_number
    idx = next((i for i, w in enumerate(plan.weeks) if w.week_number == week_num), 0)
    week = plan.weeks[idx]
    new_week, diffs, subs = apply_mutations_to_week(week, mutations, phase=week.phase)
    diff = build_diff(week, new_week, diffs, subs)
    new_plan = plan.model_copy(deep=True)
    new_plan.weeks[idx] = new_week
    return new_plan, diff
