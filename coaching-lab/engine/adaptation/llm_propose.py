"""LLM adaptation proposal — signal mapping and narrator copy within playbook bounds."""

from __future__ import annotations

import json

from engine import llm
from engine.adaptation.loader import LoadedPlaybook
from engine.adaptation.signals import SignalSummary
from engine.models import (
    AdaptationDecision,
    AthleteProfile,
    LlmAdaptationProposal,
    WeeklyContext,
    WorkoutCompletion,
)
from engine.prompts import ADAPTATION_NARRATOR_SYSTEM
from engine.weekly_context import llm_available


def build_playbook_prompt_context(loaded: LoadedPlaybook) -> str:
    spec = loaded.spec
    lines = [
        f"Playbook version: {loaded.version}",
        "",
        "Decision thresholds:",
        f"- high_rpe >= {spec.thresholds.high_rpe}",
        f"- low_readiness <= {spec.thresholds.low_readiness}",
        f"- deload at >= {spec.thresholds.deload_flag_count} flags",
        f"- hold at >= {spec.thresholds.hold_flag_count_min} flags",
        f"- illness_days_off >= {spec.thresholds.illness_days_off_threshold} -> deload reentry",
        "",
        "Guardrails:",
        f"- max weekly increase {spec.guardrails.max_weekly_increase:.0%}",
        f"- max deload reduction {spec.guardrails.max_deload_reduction:.0%}",
        "",
        "Orthopedic keywords:",
        ", ".join(spec.orthopedic_keywords),
        "",
        "GI keywords:",
        ", ".join(spec.gi_keywords),
        "",
        "Decision ladder (priority order):",
        "1. illness reentry -> deload",
        "2. run orthopedic stress -> bike_substitute",
        "3. GI stress -> gut_training",
        "4. stacked flags / consecutive holds -> deload",
        "5. warning flags -> hold",
        "6. insufficient data -> hold",
        "7. all green -> progress",
        "",
        "Narrator templates:",
    ]
    for key, tmpl in spec.narrator_templates.items():
        lines.append(f"- {key}: {tmpl[:120]}...")
    return "\n".join(lines)


def _proposal_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": [d.value for d in AdaptationDecision],
            },
            "rationale": {"type": "string"},
            "playbook_rule_cited": {"type": "string"},
            "confidence": {
                "type": "string",
                "enum": ["high", "medium", "low"],
            },
            "signal_augmentations": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "fatigue_flags": {"type": "array", "items": {"type": "string"}},
                    "illness_days_off": {"type": "integer"},
                    "life_stress": {"type": "boolean"},
                    "missed_key_reason": {"type": ["string", "null"]},
                    "athlete_quotes": {"type": "array", "items": {"type": "string"}},
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
                "required": ["summary", "fatigue_flags", "illness_days_off", "life_stress"],
            },
        },
        "required": [
            "decision",
            "rationale",
            "signal_augmentations",
            "playbook_rule_cited",
            "confidence",
        ],
    }


def _format_signals(signals: SignalSummary) -> str:
    return (
        f"flag_count={signals.flag_count}, weighted={signals.weighted_flags}, "
        f"flags={signals.flag_messages}, illness_reentry={signals.illness_reentry}, "
        f"orthopedic={signals.has_orthopedic_stress}, gi={signals.has_gi_stress}"
    )


def propose_adaptation(
    profile: AthleteProfile,
    completions: list[WorkoutCompletion],
    signals: SignalSummary,
    weekly_context: WeeklyContext,
    loaded: LoadedPlaybook,
) -> LlmAdaptationProposal | None:
    if not llm_available():
        return None

    playbook_ctx = build_playbook_prompt_context(loaded)
    user_content = (
        f"{playbook_ctx}\n\n"
        f"Weekly narrative summary: {weekly_context.summary}\n"
        f"Athlete quotes: {', '.join(weekly_context.athlete_quotes)}\n"
        f"Structured signals (workout data only): {_format_signals(signals)}\n"
        f"Injury flags: {', '.join(profile.injury_flags) or 'none'}\n"
        f"Completions in window: {len(completions)}"
    )
    raw = llm.complete_json(
        system=ADAPTATION_NARRATOR_SYSTEM,
        user_content=user_content,
        schema=_proposal_schema(),
        model=llm.extract_model(),
    )
    data = json.loads(raw)
    aug = data.get("signal_augmentations") or {}
    if weekly_context.week_number and not aug.get("week_number"):
        aug["week_number"] = weekly_context.week_number
    data["signal_augmentations"] = aug
    data["decision"] = AdaptationDecision(data["decision"])
    return LlmAdaptationProposal.model_validate(data)
