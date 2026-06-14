"""Canonical Ironman coaching ruleset.

Each rule is a hard constraint for the deterministic engine. Exceptions may be
added later via an override layer; for now every rule is mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RuleCategory(str, Enum):
    SCHEDULING = "scheduling"
    LONG_RIDE = "long_ride"
    LONG_RUN = "long_run"
    BRICK = "brick"
    INTENSITY = "intensity"
    PERIODIZATION = "periodization"
    TAPER = "taper"
    VOLUME = "volume"
    RACE_EXECUTION = "race_execution"


@dataclass(frozen=True, slots=True)
class CoachingRule:
    """A single non-negotiable coaching constraint."""

    id: str
    category: RuleCategory
    title: str
    description: str


IRONMAN_RULES: tuple[CoachingRule, ...] = (
    # --- Scheduling & weekly layout (1–20) ---
    CoachingRule(
        id="SCH-001",
        category=RuleCategory.SCHEDULING,
        title="48h between hard sessions (same discipline)",
        description=(
            "Never schedule two hard or key sessions in the same discipline "
            "within 48 hours (minimum 2 calendar days apart)."
        ),
    ),
    CoachingRule(
        id="SCH-002",
        category=RuleCategory.SCHEDULING,
        title="Key run 48h after hardest ride/brick",
        description=(
            "Place the week's key run-quality session at least 48 hours after "
            "the hardest ride or brick."
        ),
    ),
    CoachingRule(
        id="SCH-003",
        category=RuleCategory.SCHEDULING,
        title="24h between demanding sessions",
        description=(
            "Allow at least 24 hours between any two demanding sessions "
            "(key, long, brick, threshold, or VO2)."
        ),
    ),
    CoachingRule(
        id="SCH-004",
        category=RuleCategory.SCHEDULING,
        title="No same-day long ride + long run",
        description=(
            "Do not stack a standalone long ride and a standalone long run on "
            "the same calendar day. Same-day bike + run must be a deliberate "
            "brick with a capped run portion."
        ),
    ),
    CoachingRule(
        id="SCH-005",
        category=RuleCategory.SCHEDULING,
        title="48h between long bike and long run",
        description=(
            "Separate the weekly long bike and long run by at least 48 hours "
            "(minimum 2 calendar days between session days)."
        ),
    ),
    CoachingRule(
        id="SCH-006",
        category=RuleCategory.SCHEDULING,
        title="No hard run day after long ride",
        description=(
            "Do not schedule a hard or key run on the calendar day immediately "
            "after a long ride."
        ),
    ),
    CoachingRule(
        id="SCH-007",
        category=RuleCategory.SCHEDULING,
        title="Protect weekday quality after big weekends",
        description=(
            "After a long-ride / long-run weekend block, do not schedule hard "
            "run sessions on the next two weekdays (Mon–Tue when the block "
            "ends Sunday)."
        ),
    ),
    CoachingRule(
        id="SCH-008",
        category=RuleCategory.BRICK,
        title="No back-to-back high-load bricks",
        description="Never schedule high-load bricks on consecutive calendar days.",
    ),
    CoachingRule(
        id="SCH-009",
        category=RuleCategory.BRICK,
        title="Two bricks need 2+ days separation",
        description=(
            "If scheduling two bricks in one week, separate them by at least "
            "2 calendar days."
        ),
    ),
    CoachingRule(
        id="SCH-010",
        category=RuleCategory.BRICK,
        title="Max two bricks per week",
        description="Schedule at most two brick sessions per training week.",
    ),
    CoachingRule(
        id="SCH-011",
        category=RuleCategory.SCHEDULING,
        title="No race-sim brick before key long run",
        description=(
            "Do not place a race-simulation brick in the 48 hours before the "
            "week's key long run."
        ),
    ),
    CoachingRule(
        id="SCH-012",
        category=RuleCategory.SCHEDULING,
        title="Hard bike 48–72h before long ride",
        description=(
            "Place hard bike intervals at least 48 hours (2 days) before the "
            "weekly long ride or key brick."
        ),
    ),
    CoachingRule(
        id="SCH-013",
        category=RuleCategory.INTENSITY,
        title="Hard/easy weekly pattern",
        description=(
            "Follow a hard/easy pattern: demanding days must be surrounded by "
            "genuinely easy or rest days — never three demanding days in a row."
        ),
    ),
    CoachingRule(
        id="SCH-014",
        category=RuleCategory.SCHEDULING,
        title="One key endurance anchor per day",
        description=(
            "At most one key endurance anchor per day (long ride, long run, "
            "race-sim brick, or hard quality). Exception: short transition "
            "runs appended to a long ride."
        ),
    ),
    CoachingRule(
        id="SCH-015",
        category=RuleCategory.SCHEDULING,
        title="One primary quality per discipline per week",
        description=(
            "During build and peak, schedule at most one primary quality "
            "session per discipline per week."
        ),
    ),
    CoachingRule(
        id="SCH-016",
        category=RuleCategory.SCHEDULING,
        title="Rotate weekly emphasis",
        description=(
            "On brick-emphasis weeks keep standalone run quality controlled; "
            "on run-limiter weeks protect the key run and hold bike quality "
            "steady rather than stacking both."
        ),
    ),
    CoachingRule(
        id="SCH-017",
        category=RuleCategory.BRICK,
        title="Not every long ride needs a run",
        description=(
            "Only append a transition run when the session purpose requires "
            "it; routine long rides do not automatically include a run."
        ),
    ),
    CoachingRule(
        id="SCH-018",
        category=RuleCategory.SCHEDULING,
        title="Minimum one rest day per week",
        description="Include at least one full rest day (zero sessions) per week.",
    ),
    CoachingRule(
        id="SCH-019",
        category=RuleCategory.SCHEDULING,
        title="Weekend overload ceiling",
        description=(
            "Combined long ride (≥3 h) plus long run (≥90 min) on consecutive "
            "days must stay within the 48h-separation rule; never pair a 4 h+ "
            "ride with a 2 h+ run on back-to-back days."
        ),
    ),
    CoachingRule(
        id="SCH-020",
        category=RuleCategory.SCHEDULING,
        title="Strength clear of key run",
        description=(
            "Do not place strength on the same day as the key long run, or on "
            "the day immediately before it."
        ),
    ),
    # --- Long ride (21–29) ---
    CoachingRule(
        id="RIDE-021",
        category=RuleCategory.LONG_RIDE,
        title="Long ride is weekly anchor",
        description=(
            "Every non-taper training week includes exactly one long ride as "
            "the primary bike anchor."
        ),
    ),
    CoachingRule(
        id="RIDE-022",
        category=RuleCategory.LONG_RIDE,
        title="Long ride stays aerobic",
        description=(
            "Long rides are aerobic only: target IF 65–75% FTP / Zone 2. "
            "No threshold or VO2 work in the long ride."
        ),
    ),
    CoachingRule(
        id="RIDE-023",
        category=RuleCategory.LONG_RIDE,
        title="No surging on long rides",
        description=(
            "Long rides use steady power — no surges, spikes, or pass-the-rider "
            "efforts."
        ),
    ),
    CoachingRule(
        id="RIDE-024",
        category=RuleCategory.LONG_RIDE,
        title="Peak long ride 5–6 hours",
        description=(
            "Peak-phase long ride duration must not exceed 6 hours."
        ),
    ),
    CoachingRule(
        id="RIDE-025",
        category=RuleCategory.VOLUME,
        title="Bike ~50% of weekly time",
        description=(
            "Bike receives approximately 50% of weekly training time "
            "(baseline split: swim 20%, bike 50%, run 30%)."
        ),
    ),
    CoachingRule(
        id="RIDE-026",
        category=RuleCategory.BRICK,
        title="Weekly long ride may include short transition run",
        description=(
            "The weekly long ride may include an optional easy transition run "
            "of at most 20 minutes immediately after the ride."
        ),
    ),
    CoachingRule(
        id="RIDE-027",
        category=RuleCategory.PERIODIZATION,
        title="Two big days in macrocycle",
        description=(
            "The macrocycle includes exactly two big-day simulation weeks "
            "(~11 and ~5 weeks before race) with extended ride + brick run."
        ),
    ),
    CoachingRule(
        id="RIDE-028",
        category=RuleCategory.RACE_EXECUTION,
        title="Race fueling on long rides",
        description=(
            "Every long ride must include fueling notes rehearsing race-day "
            "nutrition."
        ),
    ),
    CoachingRule(
        id="RIDE-029",
        category=RuleCategory.INTENSITY,
        title="Steady pacing rehearsal",
        description=(
            "Long rides carry a steady-pacing reminder — race execution depends "
            "on even effort, not hero intervals."
        ),
    ),
    # --- Long run (30–36) ---
    CoachingRule(
        id="RUN-030",
        category=RuleCategory.LONG_RUN,
        title="Long run capped at 2.5 hours",
        description="No standalone long run may exceed 2.5 hours (9000 seconds).",
    ),
    CoachingRule(
        id="RUN-031",
        category=RuleCategory.LONG_RUN,
        title="No marathon-distance training run",
        description=(
            "Never schedule a training run at or above marathon distance "
            "(42.2 km / 26.2 mi)."
        ),
    ),
    CoachingRule(
        id="RUN-032",
        category=RuleCategory.LONG_RUN,
        title="Long runs are easy aerobic",
        description=(
            "Long runs are easy aerobic (Zone 2). No VO2 or track speed work "
            "in long runs."
        ),
    ),
    CoachingRule(
        id="RUN-033",
        category=RuleCategory.VOLUME,
        title="Run 2–3 sessions per week",
        description=(
            "Schedule 2–3 run sessions per week during Ironman build "
            "(excluding brick run portions)."
        ),
    ),
    CoachingRule(
        id="RUN-034",
        category=RuleCategory.TAPER,
        title="Final long run timing",
        description=(
            "The longest run of the macrocycle occurs 2–4 weeks before race "
            "day, then duration decreases."
        ),
    ),
    CoachingRule(
        id="RUN-035",
        category=RuleCategory.LONG_RUN,
        title="Race-pace segments when fresh",
        description=(
            "When long run is separated from long ride by ≥48 h, the session "
            "may include controlled race-pace segments; otherwise it stays "
            "fully aerobic."
        ),
    ),
    CoachingRule(
        id="RUN-036",
        category=RuleCategory.LONG_RUN,
        title="Limited true long runs per macrocycle",
        description=(
            "At most three standalone long runs (≥90 min) in any rolling "
            "4-week build block outside taper."
        ),
    ),
    # --- Brick (37–42) ---
    CoachingRule(
        id="BRK-037",
        category=RuleCategory.BRICK,
        title="Base: one short transition brick",
        description=(
            "In base phase, include at most one short transition brick per "
            "week (10–20 min easy run off the bike)."
        ),
    ),
    CoachingRule(
        id="BRK-038",
        category=RuleCategory.BRICK,
        title="Race-pace bricks every 2–3 weeks",
        description=(
            "In build/peak, race-pace simulation bricks occur at most once "
            "every 2–3 weeks."
        ),
    ),
    CoachingRule(
        id="BRK-039",
        category=RuleCategory.BRICK,
        title="Brick run cap off long ride",
        description=(
            "Off a ride ≥4 hours, the attached run portion must not exceed "
            "90 minutes."
        ),
    ),
    CoachingRule(
        id="BRK-040",
        category=RuleCategory.BRICK,
        title="Brick run starts easy",
        description=(
            "Brick runs begin at easy effort; if form breaks, the run portion "
            "is too long or too hard."
        ),
    ),
    CoachingRule(
        id="BRK-041",
        category=RuleCategory.BRICK,
        title="Brick weekend replaces split long days",
        description=(
            "On race-simulation brick weekends, do not also schedule a "
            "separate long ride and long run on adjacent days."
        ),
    ),
    CoachingRule(
        id="BRK-042",
        category=RuleCategory.BRICK,
        title="Peak sim brick frequency",
        description=(
            "At most two peak simulation bricks (≥4 h ride + ≥60 min run) "
            "in the final 6 weeks before race day."
        ),
    ),
    # --- Intensity distribution (43–47) ---
    CoachingRule(
        id="INT-043",
        category=RuleCategory.INTENSITY,
        title="80/20 intensity distribution",
        description=(
            "When weekly volume exceeds 7 hours, at least 80% of session "
            "time must be low intensity (aerobic base, recovery, easy economy)."
        ),
    ),
    CoachingRule(
        id="INT-044",
        category=RuleCategory.INTENSITY,
        title="80/20 mandatory above 15 h/week",
        description=(
            "When weekly volume exceeds 15 hours, the 80/20 split is mandatory "
            "— no exceptions."
        ),
    ),
    CoachingRule(
        id="INT-045",
        category=RuleCategory.INTENSITY,
        title="Avoid grey-zone stacking",
        description=(
            "Do not label easy sessions as moderate; supporting endurance "
            "rides and runs must use aerobic_base or recovery purpose tags."
        ),
    ),
    CoachingRule(
        id="INT-046",
        category=RuleCategory.INTENSITY,
        title="Hard days truly hard",
        description=(
            "Quality sessions (threshold, VO2, race_execution) must be "
            "flagged is_key_session=True so the hard/easy pattern is visible."
        ),
    ),
    CoachingRule(
        id="INT-047",
        category=RuleCategory.INTENSITY,
        title="IM run intervals stay comfortable",
        description=(
            "Run quality work stays sub-threshold and comfortable — use "
            "threshold or economy tags, never VO2, for Ironman run intervals."
        ),
    ),
    # --- Periodization & recovery (48–50) ---
    CoachingRule(
        id="PER-048",
        category=RuleCategory.PERIODIZATION,
        title="3:1 load–recovery microcycle",
        description=(
            "Every 4th training week is a recovery (deload) week with 30–40% "
            "volume reduction."
        ),
    ),
    CoachingRule(
        id="PER-049",
        category=RuleCategory.PERIODIZATION,
        title="Recovery week keeps frequency",
        description=(
            "Deload weeks reduce duration, not session count — maintain "
            "frequency with shorter easy sessions."
        ),
    ),
    CoachingRule(
        id="PER-050",
        category=RuleCategory.PERIODIZATION,
        title="Unplanned recovery block allowed",
        description=(
            "The adaptation layer may insert a 3–5 day recovery block when "
            "accumulated fatigue signals demand it (handled by adaptation, "
            "not overridden by scheduling)."
        ),
    ),
    # --- Taper (bonus hard rules referenced by engine) ---
    CoachingRule(
        id="TAP-051",
        category=RuleCategory.TAPER,
        title="Taper volume steps",
        description=(
            "Taper reduces volume progressively (~75% → 50% → 25% of peak) "
            "while keeping frequency."
        ),
    ),
    CoachingRule(
        id="TAP-052",
        category=RuleCategory.TAPER,
        title="No long run inside 10 days",
        description="No run ≥90 minutes inside 10 days of race day.",
    ),
    CoachingRule(
        id="TAP-053",
        category=RuleCategory.TAPER,
        title="No long bike inside 7 days",
        description="No ride ≥3 hours inside 7 days of race day.",
    ),
    CoachingRule(
        id="TAP-054",
        category=RuleCategory.TAPER,
        title="Maintain taper intensity",
        description=(
            "During taper, shorten sessions but keep short race-pace touches — "
            "do not drop all quality."
        ),
    ),
    CoachingRule(
        id="TAP-055",
        category=RuleCategory.TAPER,
        title="No catch-up in taper",
        description="Never schedule make-up sessions during taper weeks.",
    ),
)

RULE_BY_ID: dict[str, CoachingRule] = {r.id: r for r in IRONMAN_RULES}
