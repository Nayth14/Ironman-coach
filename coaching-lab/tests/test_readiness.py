"""Tests for engine.readiness — deterministic readiness assessment."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from engine.models import (
    AthleteProfile,
    ExperienceLevel,
    ReadinessVerdict,
)
from engine.readiness import assess, weeks_to_race


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _profile(
    *,
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER,
    race_date: date = date(2027, 6, 1),
    weekly_hours: float = 10,
    injury_flags: list[str] | None = None,
) -> AthleteProfile:
    return AthleteProfile(
        goal_type="finish",
        race_name="Test IM",
        race_date=race_date,
        weekly_hours=weekly_hours,
        limiter_discipline="run",
        experience_level=experience_level,
        available_days=[0, 1, 2, 3, 4, 5, 6],
        injury_flags=injury_flags or [],
    )


# ---------------------------------------------------------------------------
# weeks_to_race
# ---------------------------------------------------------------------------

class TestWeeksToRace:
    def test_exact_weeks(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=20)
        assert weeks_to_race(race, today) == 20

    def test_partial_week_rounds_down(self):
        today = date(2027, 1, 1)
        race = today + timedelta(days=15)  # 2 weeks + 1 day
        assert weeks_to_race(race, today) == 2

    def test_race_in_past_returns_zero(self):
        today = date(2027, 6, 1)
        race = date(2027, 5, 1)
        assert weeks_to_race(race, today) == 0

    def test_race_today_returns_zero(self):
        today = date(2027, 6, 1)
        assert weeks_to_race(today, today) == 0

    def test_defaults_to_today(self):
        far_future = date.today() + timedelta(weeks=52)
        result = weeks_to_race(far_future)
        assert result >= 51


# ---------------------------------------------------------------------------
# assess — GREEN scenarios
# ---------------------------------------------------------------------------

class TestAssessGreen:
    def test_beginner_comfortable_runway(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=35)  # >30 comfortable
        result = assess(_profile(race_date=race), today)
        assert result.verdict == ReadinessVerdict.GREEN
        assert result.weeks_to_race == 35
        assert result.adjustments == []

    def test_intermediate_comfortable_runway(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=22)  # >20 comfortable for intermediate
        result = assess(
            _profile(experience_level=ExperienceLevel.INTERMEDIATE, race_date=race),
            today,
        )
        assert result.verdict == ReadinessVerdict.GREEN

    def test_advanced_comfortable_runway(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=18)  # >16 comfortable for advanced
        result = assess(
            _profile(experience_level=ExperienceLevel.ADVANCED, race_date=race),
            today,
        )
        assert result.verdict == ReadinessVerdict.GREEN


# ---------------------------------------------------------------------------
# assess — AMBER scenarios
# ---------------------------------------------------------------------------

class TestAssessAmber:
    def test_beginner_short_but_workable(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=20)  # <24 min but >= 24*0.6=14.4
        result = assess(_profile(race_date=race), today)
        assert result.verdict == ReadinessVerdict.AMBER
        assert any("short" in f.lower() or "bit short" in f.lower() for f in [result.rationale])
        assert "Compress base phase" in result.adjustments[0]

    def test_low_weekly_hours_single_flag(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=35)
        result = assess(_profile(race_date=race, weekly_hours=5), today)
        assert result.verdict == ReadinessVerdict.AMBER
        assert any("Cap intensity" in a for a in result.adjustments)

    def test_single_injury_with_short_timeline(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=20)  # short timeline flag
        result = assess(
            _profile(race_date=race, injury_flags=["knee"]),
            today,
        )
        assert result.verdict == ReadinessVerdict.AMBER
        assert any("knee" in a for a in result.adjustments)


# ---------------------------------------------------------------------------
# assess — RED scenarios
# ---------------------------------------------------------------------------

class TestAssessRed:
    def test_very_short_timeline_beginner(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=10)  # <24*0.6=14.4
        result = assess(_profile(race_date=race), today)
        assert result.verdict == ReadinessVerdict.RED
        assert "conservative" in result.adjustments[0].lower() or "later" in result.adjustments[0].lower()

    def test_two_flags_trigger_red(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=20)  # short (amber flag)
        result = assess(
            _profile(race_date=race, weekly_hours=5),  # low hours (amber flag)
            today,
        )
        assert result.verdict == ReadinessVerdict.RED

    def test_multiple_injuries_plus_short_timeline(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=10)
        result = assess(
            _profile(race_date=race, injury_flags=["knee", "plantar_fasciitis"]),
            today,
        )
        assert result.verdict == ReadinessVerdict.RED
        assert len(result.adjustments) >= 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestAssessEdgeCases:
    def test_two_injuries_alone(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=35)
        result = assess(
            _profile(race_date=race, injury_flags=["knee", "achilles"]),
            today,
        )
        assert any("Multiple injury" in result.rationale for _ in [1])
        assert any("Conservative" in a for a in result.adjustments)

    def test_race_date_is_today_returns_zero_weeks(self):
        today = date(2027, 6, 1)
        result = assess(_profile(race_date=today), today)
        assert result.weeks_to_race == 0
        assert result.verdict == ReadinessVerdict.RED

    def test_intermediate_exact_min_threshold(self):
        today = date(2027, 1, 1)
        race = today + timedelta(weeks=16)  # exactly min for intermediate
        result = assess(
            _profile(experience_level=ExperienceLevel.INTERMEDIATE, race_date=race),
            today,
        )
        # 16 weeks = min, but not comfortable (20); still flags => amber
        assert result.verdict == ReadinessVerdict.AMBER
