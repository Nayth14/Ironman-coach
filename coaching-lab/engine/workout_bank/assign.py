from __future__ import annotations

from engine.models import PhaseName, PlanState, PlannedWeek, Sport
from engine.workout_bank.load import all_bank_workouts
from engine.workout_bank.select import is_bank_eligible, pick_bank_workout


class SwimBankAssignmentError(Exception):
    """Raised when a swim workout cannot be matched to the swim workout bank."""


def _apply_bank_entry(workout, entry, state: PlanState) -> None:
    workout.bank_workout_id = entry.id
    workout.title = entry.title
    workout.description = entry.main_set
    workout.purpose_tag = entry.purpose_tag
    workout.is_key_session = entry.is_key_session
    workout.estimated_tss = entry.estimated_tss
    state.used_bank_ids.append(entry.id)


def assign_bank_workouts(
    week: PlannedWeek,
    *,
    phase: PhaseName,
    state: PlanState,
) -> PlannedWeek:
    bank_workouts = all_bank_workouts()
    for workout in week.workouts:
        if not is_bank_eligible(workout, is_deload=week.is_deload):
            continue
        entry = pick_bank_workout(
            workout,
            phase=phase,
            week_number=week.week_number,
            is_deload=week.is_deload,
            state=state,
            bank_workouts=bank_workouts,
        )
        if not entry:
            if workout.sport == Sport.SWIM:
                minutes = max(1, round((workout.estimated_duration_seconds or 0) / 60))
                raise SwimBankAssignmentError(
                    f"No swim bank workout matched for '{workout.title}' "
                    f"({minutes} min, phase={phase.value}, deload={week.is_deload})"
                )
            continue

        _apply_bank_entry(workout, entry, state)
    return week
