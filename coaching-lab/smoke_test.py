"""Offline smoke test for the coaching engine (no OpenAI required).

Runs every saved fixture through readiness, strength, periodization, scheduling,
and a sample adaptation. Use this to sanity-check rule changes quickly:

    python smoke_test.py
"""

from __future__ import annotations

from engine import adaptation, fixtures, plan as plan_builder, readiness, strength
from engine.models import Sport, WorkoutCompletion
from engine.rules import IRONMAN_RULES, validate_plan


def run() -> None:
    for stem in fixtures.list_fixtures():
        name, profile = fixtures.load_fixture(stem)
        print("=" * 70)
        print(f"PERSONA: {name}  ({stem})")
        print("-" * 70)

        verdict = readiness.assess(profile)
        print(f"Readiness: {verdict.verdict.value.upper()} "
              f"({verdict.weeks_to_race} wks)")
        print(f"  {verdict.rationale}")
        for adj in verdict.adjustments:
            print(f"  - {adj}")

        sp = strength.prescribe(profile)
        exercises = strength.select_exercises(profile)
        print(f"Strength: {sp.sessions_per_week}x/wk, {sp.session_duration_minutes}min")
        print(f"  Focus: {sp.focus}")
        print(f"  Restrictions: {sp.restrictions or 'none'}")
        print(f"  Exercises: {', '.join(e.name for e in exercises)}")

        tp = plan_builder.generate_plan(profile)
        violations = validate_plan(tp)
        print(f"Rules: {len(IRONMAN_RULES)} hard rules, {len(violations)} violations")
        print(f"Plan: {tp.total_weeks} weeks, {len(tp.phases)} phases")
        for p in tp.phases:
            print(f"  {p.name.value:6s} wk {p.start_week}-{p.end_week}")

        if tp.weeks:
            wk = tp.weeks[0]
            print(f"Week 1 ({wk.phase.value}, {wk.target_hours}h, "
                  f"{len(wk.workouts)} sessions):")
            for w in wk.workouts:
                mins = (w.estimated_duration_seconds or 0) // 60
                key = " [KEY]" if w.is_key_session else ""
                print(f"  {w.sport.value:8s} {w.title:18s} {mins:3d}min{key}")

            # Sample adaptation: simulate a fatigued week.
            sims = [
                WorkoutCompletion(
                    workout_id=w.id, sport=w.sport, completed=True, rpe=9
                )
                for w in wk.workouts
            ]
            if sims:
                sims[0].fatigue_flags = ["poor sleep"]
                sims[0].readiness_score = 3
            result = adaptation.evaluate(profile, sims)
            print(f"Adaptation (high RPE + poor sleep): {result.decision.value}")
            print(f"  {result.rationale}")

        print()

    print("Smoke test complete.")


if __name__ == "__main__":
    run()
