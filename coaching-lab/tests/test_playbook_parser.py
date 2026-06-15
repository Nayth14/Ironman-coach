"""Tests for Adaptation Playbook loader and parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.adaptation.loader import clear_cache, load_playbook
from engine.adaptation.parser import parse_playbook_file, parse_yaml_file

PLAYBOOK_DIR = Path(__file__).resolve().parents[1] / "playbook"


def test_load_playbook_from_markdown():
    clear_cache()
    loaded = load_playbook(PLAYBOOK_DIR / "Adaptation-Playbook.md")
    assert loaded.version == "1.0"
    assert loaded.checksum
    assert loaded.spec.thresholds.high_rpe == 8
    assert loaded.spec.guardrails.max_weekly_increase == 0.10
    assert len(loaded.spec.golden_scenarios) >= 12


def test_load_playbook_from_yaml_fallback():
    clear_cache()
    loaded = load_playbook(PLAYBOOK_DIR / "playbook-data.yaml")
    assert loaded.spec.decisions["progress"].entry.min_completed_sessions == 3


def test_playbook_has_all_decisions():
    loaded = load_playbook()
    for name in ("progress", "hold", "deload", "bike_substitute", "gut_training"):
        assert name in loaded.spec.decisions


def test_checksum_cache():
    clear_cache()
    a = load_playbook()
    b = load_playbook()
    assert a.checksum == b.checksum
