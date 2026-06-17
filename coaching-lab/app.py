"""Streamlit coaching lab for Nayth's Ironman Coach.

Thin UI over the `engine` package. Use this to nail the coaching logic before
building the main app. The app does NOT contain coaching decisions — all of
that lives in `engine/`.

Run:  streamlit run app.py
"""

from __future__ import annotations

import json

import streamlit as st
from dotenv import load_dotenv

from engine import adaptation, extract, fixtures, plan as plan_builder, readiness, strength
from engine import llm
from engine.adaptation.apply import apply_mutations_to_plan
from engine.adaptation.trajectory import apply_plan_state_delta
from engine.models import (
    AdaptationResult,
    AthleteProfile,
    PlanState,
    PurposeTag,
    Sport,
    WorkoutCompletion,
)
from engine.prompts import ONBOARDING_SYSTEM, SUMMARY_SYSTEM

load_dotenv()

st.set_page_config(page_title="Coaching Lab — Nayth's Ironman Coach", layout="wide")

SPORT_EMOJI = {
    Sport.SWIM: "🏊",
    Sport.BIKE: "🚴",
    Sport.RUN: "🏃",
    Sport.STRENGTH: "🏋️",
    Sport.BRICK: "🔁",
    Sport.OTHER: "•",
}


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------


def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("readiness", None)
    st.session_state.setdefault("plan", None)
    st.session_state.setdefault("plan_state", PlanState())
    st.session_state.setdefault("pending_adaptation", None)
    st.session_state.setdefault("summary", None)


def _reset() -> None:
    for key in ["messages", "profile", "readiness", "plan", "summary", "pending_adaptation"]:
        st.session_state[key] = [] if key == "messages" else None
    st.session_state.plan_state = PlanState()


# ---------------------------------------------------------------------------
# Plan building
# ---------------------------------------------------------------------------


def _build_from_profile(profile: AthleteProfile) -> None:
    st.session_state.profile = profile
    st.session_state.readiness = readiness.assess(profile)
    st.session_state.plan = plan_builder.generate_plan(profile)
    st.session_state.plan_state = PlanState()
    st.session_state.pending_adaptation = None


def _workout_is_optional(w) -> bool:
    return not w.is_key_session and w.purpose_tag in (
        PurposeTag.AEROBIC_BASE,
        PurposeTag.ECONOMY,
        PurposeTag.RECOVERY,
    )


def _generate_summary() -> str:
    profile = st.session_state.profile
    verdict = st.session_state.readiness
    tp = st.session_state.plan
    phase_lines = ", ".join(
        f"{p.name.value} (wk {p.start_week}-{p.end_week})" for p in tp.phases
    )
    context = (
        f"Profile: {profile.model_dump_json()}\n"
        f"Readiness: {verdict.model_dump_json()}\n"
        f"Strength plan: {tp.strength_plan.model_dump_json()}\n"
        f"Phases: {phase_lines}\n"
        f"Weeks materialized: {len(tp.weeks)}"
    )
    return llm.complete_chat(
        system=SUMMARY_SYSTEM,
        messages=[{"role": "user", "content": context}],
        model=llm.summary_model(),
    )


# ---------------------------------------------------------------------------
# Sidebar: fixtures + controls
# ---------------------------------------------------------------------------


def _render_sidebar() -> None:
    st.sidebar.title("Coaching Lab")
    st.sidebar.caption("Validate the coach before building the main app.")

    st.sidebar.subheader("Load a persona")
    options = ["—"] + fixtures.list_fixtures()
    choice = st.sidebar.selectbox("Skip the chat with a saved profile", options)
    if choice != "—" and st.sidebar.button("Build plan from persona"):
        name, profile = fixtures.load_fixture(choice)
        _build_from_profile(profile)
        st.session_state.summary = None
        st.session_state.messages = [
            {"role": "assistant", "content": f"Loaded persona **{name}** and built a plan."}
        ]
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Reset session"):
        _reset()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.caption(
        f"Chat model: `{llm.chat_model()}`  \n"
        f"Extract model: `{llm.extract_model()}`  \n"
        f"Summary model: `{llm.summary_model()}`"
    )


# ---------------------------------------------------------------------------
# Chat column
# ---------------------------------------------------------------------------


def _render_chat() -> None:
    st.subheader("Onboarding coach")

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_input = st.chat_input("Talk to your coach…")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream the coach reply.
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        try:
            for delta in llm.stream_chat(ONBOARDING_SYSTEM, st.session_state.messages):
                full += delta
                placeholder.markdown(extract.strip_ready_token(full) + "▌")
            placeholder.markdown(extract.strip_ready_token(full))
        except Exception as exc:  # noqa: BLE001 - surface errors in the lab UI
            placeholder.error(f"OpenAI error: {exc}")
            return

    st.session_state.messages.append(
        {"role": "assistant", "content": extract.strip_ready_token(full)}
    )

    # When the coach signals readiness, extract + build.
    if extract.conversation_is_ready(full):
        with st.spinner("Extracting profile and building plan…"):
            try:
                profile = extract.extract_profile(st.session_state.messages)
                _build_from_profile(profile)
                st.session_state.summary = _generate_summary()
            except ValueError as exc:
                st.warning(str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                st.error(f"Plan generation failed: {exc}")
                return
        st.rerun()


# ---------------------------------------------------------------------------
# Inspection column
# ---------------------------------------------------------------------------


def _render_profile() -> None:
    profile: AthleteProfile = st.session_state.profile
    st.markdown("**Extracted profile**")
    st.json(json.loads(profile.model_dump_json()))


def _render_readiness() -> None:
    verdict = st.session_state.readiness
    colors = {"green": "🟢", "amber": "🟡", "red": "🔴"}
    st.markdown(
        f"**Readiness:** {colors.get(verdict.verdict.value, '')} "
        f"{verdict.verdict.value.upper()} — {verdict.weeks_to_race} weeks to race"
    )
    st.caption(verdict.rationale)
    if verdict.adjustments:
        for a in verdict.adjustments:
            st.markdown(f"- {a}")


def _render_strength() -> None:
    tp = st.session_state.plan
    sp = tp.strength_plan
    st.markdown("**Strength plan**")
    st.markdown(
        f"{sp.sessions_per_week}x/week · {sp.session_duration_minutes} min · {sp.focus}"
    )
    st.caption(sp.rationale)
    exercises = strength.select_exercises(st.session_state.profile)
    if exercises:
        st.markdown("Sample exercises: " + ", ".join(e.name for e in exercises))


def _render_phases() -> None:
    tp = st.session_state.plan
    st.markdown(f"**Macrocycle** ({tp.total_weeks} weeks)")
    rows = [
        {
            "Phase": p.name.value,
            "Weeks": f"{p.start_week}–{p.end_week}",
            "Objective": p.objective,
        }
        for p in tp.phases
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def _render_weeks() -> None:
    tp = st.session_state.plan
    st.markdown("**Materialized weeks**")
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for wk in tp.weeks:
        label = f"Week {wk.week_number} · {wk.phase.value}"
        if wk.is_deload:
            label += " · deload"
        label += f" · {wk.target_hours}h"
        with st.expander(label, expanded=(wk.week_number == 1)):
            rows = []
            for w in wk.workouts:
                day = day_names[w.day_of_week] if w.day_of_week is not None else "—"
                mins = (w.estimated_duration_seconds or 0) // 60
                rows.append(
                    {
                        "Day": day,
                        "Sport": f"{SPORT_EMOJI.get(w.sport, '')} {w.sport.value}",
                        "Workout": w.title,
                        "Key": "★" if w.is_key_session else "",
                        "Min": mins,
                        "Purpose": w.purpose_tag.value,
                    }
                )
            st.dataframe(rows, hide_index=True, use_container_width=True)


def _render_adaptation_result(result: AdaptationResult) -> None:
    decision_color = {
        "progress": "🟢",
        "hold": "🟡",
        "deload": "🔴",
        "bike_substitute": "🔵",
        "gut_training": "🟠",
    }
    st.markdown(
        f"### {decision_color.get(result.decision.value, '')} "
        f"{result.decision.value.replace('_', ' ').title()}"
    )
    if result.reviewed_week_number is not None and result.target_week_number is not None:
        st.info(
            f"Based on **week {result.reviewed_week_number}** feedback → "
            f"changes apply to **week {result.target_week_number}**."
        )
    elif result.reviewed_week_number is not None and result.target_week_number is None:
        st.info(
            f"Based on **week {result.reviewed_week_number}** feedback → "
            "workout changes will apply when the next week is materialized "
            "(trajectory updated now)."
        )
    st.caption(result.rationale)
    if result.insufficient_data:
        st.warning("Insufficient completion data — engine will hold until more feedback is logged.")
    st.markdown("**Signals**")
    for s in result.signals:
        st.markdown(f"- {s}")
    st.markdown("**Changes**")
    for c in result.changes:
        st.markdown(f"- {c}")
    if result.diff:
        st.markdown("**Preview**")
        st.markdown(
            f"Weekly hours: **{result.diff.before_hours:.1f}h** → "
            f"**{result.diff.after_hours:.1f}h**"
        )
        for w in result.diff.changed_workouts:
            st.markdown(f"- {w.title}: {w.change_summary}")
        for sub in result.diff.substitutions:
            st.markdown(f"- ↔ {sub}")
    if result.playbook_version:
        st.caption(f"Ruleset v{result.playbook_version}")


def _apply_pending_adaptation(result: AdaptationResult) -> None:
    tp = st.session_state.plan
    if result.mutations and tp.weeks and result.target_week_number is not None:
        new_plan, _ = apply_mutations_to_plan(
            tp, result.mutations, result.target_week_number
        )
        st.session_state.plan = new_plan
    if result.plan_state_delta:
        st.session_state.plan_state = apply_plan_state_delta(
            st.session_state.plan_state, result.plan_state_delta
        )


def _render_adaptation_sim() -> None:
    st.markdown("**Simulate a week of feedback**")
    st.caption(
        "Log how week 1 went, evaluate, then accept to update **week 2** above."
    )

    tp = st.session_state.plan
    reviewed_week = tp.weeks[0] if tp.weeks else None
    if not reviewed_week:
        return

    pending: AdaptationResult | None = st.session_state.pending_adaptation

    st.markdown(f"**Week {reviewed_week.week_number} workouts**")
    completions: list[WorkoutCompletion] = []
    with st.form("sim_form"):
        for w in reviewed_week.workouts:
            cols = st.columns([3, 1, 1])
            key_tag = " ★" if w.is_key_session else ""
            cols[0].markdown(f"{SPORT_EMOJI.get(w.sport, '')} {w.title}{key_tag}")
            done = cols[1].checkbox("Done", value=True, key=f"done_{w.id}")
            rpe = cols[2].slider("RPE", 1, 10, 5, key=f"rpe_{w.id}")
            completions.append(
                WorkoutCompletion(
                    workout_id=w.id,
                    sport=w.sport,
                    completed=done,
                    rpe=rpe,
                    is_key_session=w.is_key_session,
                    is_optional=_workout_is_optional(w),
                    week_number=reviewed_week.week_number,
                )
            )
        fatigue = st.text_input(
            "Fatigue flags (comma-separated, e.g. 'left knee, poor sleep')", ""
        )
        weekly_notes = st.text_area(
            "Anything else that happened this week (natural language)",
            "",
            height=80,
        )
        submitted = st.form_submit_button("Evaluate adaptation")

    if submitted:
        from engine.models import WeeklyContext

        weekly_context = None
        if fatigue.strip():
            tags = [t.strip() for t in fatigue.split(",") if t.strip()]
            if completions:
                completions[0].fatigue_flags = tags
        if weekly_notes.strip():
            flags = [t.strip() for t in fatigue.split(",") if t.strip()] if fatigue.strip() else []
            weekly_context = WeeklyContext(
                summary=weekly_notes.strip()[:200],
                fatigue_flags=flags,
                life_stress=any(
                    k in weekly_notes.lower()
                    for k in ("sleep", "stress", "travel", "work")
                ),
            )
        st.session_state.pending_adaptation = adaptation.evaluate(
            st.session_state.profile,
            completions,
            plan_state=st.session_state.plan_state,
            plan=tp,
            reviewed_week_number=reviewed_week.week_number,
            weekly_context=weekly_context,
        )
        st.rerun()

    if pending:
        st.divider()
        st.markdown("**Pending adaptation**")
        _render_adaptation_result(pending)
        accept_col, dismiss_col = st.columns(2)
        if accept_col.button("Accept changes", type="primary", key="adapt_accept"):
            _apply_pending_adaptation(pending)
            st.session_state.pending_adaptation = None
            target = pending.target_week_number
            st.success(
                f"Plan updated — see week {target} in materialized weeks above."
                if target
                else "Trajectory updated — see materialized weeks above."
            )
            st.rerun()
        if dismiss_col.button("Dismiss", key="adapt_dismiss"):
            st.session_state.pending_adaptation = None
            st.rerun()


def _render_inspection() -> None:
    if not st.session_state.plan:
        st.info("Talk to the coach (or load a persona) to generate a plan.")
        return

    if st.session_state.summary:
        st.success(st.session_state.summary)

    _render_profile()
    st.divider()
    _render_readiness()
    st.divider()
    _render_strength()
    st.divider()
    _render_phases()
    st.divider()
    _render_weeks()
    st.divider()
    _render_adaptation_sim()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    _init_state()
    _render_sidebar()

    st.title("🏊 🚴 🏃 Coaching Lab")
    st.caption(
        "Validate the coaching logic for Nayth's Ironman Coach. "
        "All decisions live in the `engine/` package."
    )

    left, right = st.columns([1, 1])
    with left:
        _render_chat()
    with right:
        _render_inspection()


if __name__ == "__main__":
    main()
