from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "workouts"
OUT = ROOT / "coaching-lab" / "engine" / "workout_bank" / "data"

ID_RE = re.compile(r"^(SS|TH|OU|TMP|FI|LR|TECH|AER|THR)(\d+)-(\d+)$")
TSS_RE = re.compile(r"~(\d+(?:\.\d+)?)")


def _parse_tss(raw: str) -> float | None:
    m = TSS_RE.search(raw)
    if not m:
        return None
    return float(m.group(1))


def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _purpose_and_family(prefix: str, sport: str, duration: int, variant: int) -> tuple[str, str]:
    if prefix == "TECH":
        return "economy", "technique"
    if prefix == "AER":
        return "aerobic_base", "aerobic_fitness"
    if prefix == "THR":
        return "threshold", "threshold_fitness"
    if prefix == "SS":
        return "threshold", "sweet_spot"
    if prefix == "TH":
        return "threshold", "threshold"
    if prefix == "OU":
        return "threshold", "over_under"
    if prefix == "TMP":
        return "threshold", "tempo"
    if prefix == "FI":
        return "vo2", "fast_interval"
    if prefix == "LR":
        if sport == "bike":
            if variant == 1:
                return "aerobic_base", "long_steady"
            if variant == 2:
                return "durability", "long_tempo"
            if variant == 3:
                return "race_execution", "long_race_pace"
            if variant == 4:
                return "aerobic_base", "long_progressive"
            return "race_execution", "long_durability"
        if variant == 1:
            return "aerobic_base", "long_conversational"
        if variant == 2:
            return "race_execution", "long_race_blocks"
        if variant == 3:
            if duration >= 150:
                return "durability", "long_fast_finish"
            return "race_execution", "long_fast_finish"
        return "race_execution", "long_race_blocks"
    raise ValueError(prefix)


def _warmup_cooldown_minutes(sport: str, duration: int, category: str) -> tuple[int, int]:
    if category == "long":
        return (10, 10)
    if sport == "swim":
        if duration <= 45:
            return (8, 5)
        if duration <= 50:
            return (10, 6)
        if duration <= 60:
            return (10, 5)
        if duration <= 75:
            return (12, 5)
        return (15, 7)
    if sport == "run":
        if duration == 45:
            return (12, 8)
        if duration == 60:
            return (15, 10)
        return (15, 10)
    if duration == 45:
        return (10, 5)
    if duration == 60:
        return (12, 8)
    return (15, 10)


def _phases_for_family(family: str) -> list[str]:
    if family in {"technique", "aerobic_fitness"}:
        return ["prep", "base", "build", "peak", "taper"]
    if family in {"threshold_fitness"}:
        return ["build", "peak"]
    if family in {"sweet_spot", "tempo", "long_conversational", "long_steady", "long_progressive"}:
        return ["prep", "base", "build", "peak"]
    if family in {"over_under", "threshold", "fast_interval", "long_tempo", "long_race_blocks", "long_race_pace", "long_fast_finish", "long_durability"}:
        return ["build", "peak"]
    return ["prep", "base", "build", "peak"]


def parse_bank(path: Path, sport: str) -> list[dict]:
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cols = _split_row(line)
        if len(cols) < 5:
            continue
        m = ID_RE.match(cols[0])
        if not m:
            continue
        prefix, duration_s, variant_s = m.groups()
        duration = int(duration_s)
        variant = int(variant_s)
        category = "long" if prefix == "LR" else "interval"
        purpose_tag, family = _purpose_and_family(prefix, sport, duration, variant)
        warm, cool = _warmup_cooldown_minutes(sport, duration, category)
        intensity_hint = cols[-2]
        if category == "long":
            main_set = cols[2]
            title = cols[1]
        else:
            title = cols[1]
            main_set = cols[2]
        is_key = True
        if sport == "swim" and prefix == "AER":
            is_key = False
        rows.append(
            {
                "id": cols[0],
                "sport": sport,
                "category": category,
                "family": family,
                "title": title,
                "main_set": main_set,
                "duration_minutes": duration,
                "purpose_tag": purpose_tag,
                "is_key_session": is_key,
                "estimated_tss": _parse_tss(cols[-1]),
                "intensity_hint": intensity_hint,
                "phases": _phases_for_family(family),
                "warmup_minutes": warm,
                "cooldown_minutes": cool,
            }
        )
    rows.sort(key=lambda r: r["id"])
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cycling = parse_bank(DOCS / "cycling-workout-bank.md", "bike")
    running = parse_bank(DOCS / "running-workout-bank.md", "run")
    swimming = parse_bank(DOCS / "swimming-workout-bank.md", "swim")
    (OUT / "cycling.json").write_text(json.dumps(cycling, indent=2) + "\n", encoding="utf-8")
    (OUT / "running.json").write_text(json.dumps(running, indent=2) + "\n", encoding="utf-8")
    (OUT / "swimming.json").write_text(json.dumps(swimming, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {len(cycling)} cycling, {len(running)} running, "
        f"and {len(swimming)} swimming workouts"
    )


if __name__ == "__main__":
    main()
