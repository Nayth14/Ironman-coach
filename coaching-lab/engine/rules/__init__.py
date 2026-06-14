"""Ironman coaching rules — hard constraints the engine must satisfy.

All rules are defined in ``ruleset.IRONMAN_RULES`` and enforced by
``validate`` (post-build check) and ``placement`` (schedule builder).
"""

from engine.rules.placement import schedule_week
from engine.rules.ruleset import IRONMAN_RULES, CoachingRule, RuleCategory
from engine.rules.validate import (
    RuleContext,
    RuleViolation,
    assert_plan_valid,
    validate_plan,
    validate_week,
)

__all__ = [
    "IRONMAN_RULES",
    "CoachingRule",
    "RuleCategory",
    "RuleContext",
    "RuleViolation",
    "assert_plan_valid",
    "schedule_week",
    "validate_plan",
    "validate_week",
]
