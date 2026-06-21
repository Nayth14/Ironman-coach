# Swimming Workout Bank

A reference library of **structured pool swim workouts** for the Ironman coach planner.
Each session follows **warm-up → technique set → fitness set → cool-down**, with total
volume typically **2000–4000 m** depending on session length.

Intensities use **RPE** and **CSS-relative pace** where known; the planner expands
main-set shorthand into structured `WorkoutStep`s.

---

## How to use this bank

1. **Pick by session duration first** (the plan slots 45 / 50 / 60 / 75 / 90 min swims),
   then by **family** (technique vs aerobic fitness vs threshold fitness).
2. **Phase guidance**
   - **Prep / Base:** lean on `TECH` (technique) and `AER` (aerobic fitness).
   - **Build / Peak:** add `THR` (threshold fitness); keep one technique-focused swim per week.
   - **Taper / Deload:** `TECH` and easy `AER` only.
3. **Every prescribed swim** in the plan must map to an entry in this bank.

Interval ID scheme: `TECH` technique · `AER` aerobic fitness · `THR` threshold fitness,
followed by duration in minutes and variant index (e.g. `TECH60-2`).

---

## Index

- [45-minute sessions (9)](#45-minute-sessions)
- [50-minute sessions (9)](#50-minute-sessions)
- [60-minute sessions (9)](#60-minute-sessions)
- [75-minute sessions (9)](#75-minute-sessions)
- [90-minute sessions (9)](#90-minute-sessions)
- [Mapping to the planner](#mapping-to-the-planner)

---

# 45-minute sessions

Warm-up ~400 m, technique ~300 m, fitness ~800–1000 m, cool-down ~200 m.

## Technique — 45 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| TECH45-1 | Catch-Up Focus | WU 400 + 6×50 drill/swim + 8×100 aerobic steady + CD 200 | RPE 2–4 | ~35 |
| TECH45-2 | Fingertip & Single-Arm | WU 400 + 8×50 (25 drill/25 swim) + 6×100 moderate + CD 200 | RPE 2–5 | ~36 |
| TECH45-3 | Scull & Feel | WU 400 + 6×75 (25 scull/25 kick/25 swim) + 4×100 steady + CD 200 | RPE 2–4 | ~34 |

## Aerobic fitness — 45 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| AER45-1 | Aerobic 100s | WU 400 + 4×50 drill/swim + 10×100 aerobic (15s rest) + CD 200 | RPE 3–4 | ~38 |
| AER45-2 | Pull Tempo | WU 400 + 6×50 drill/swim + 3×200 pull steady + CD 200 | RPE 3–5 | ~40 |
| AER45-3 | Build 50s | WU 400 + 6×50 drill/swim + 4×50 build 1–4 + 6×100 steady + CD 200 | RPE 3–5 | ~39 |

## Threshold fitness — 45 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| THR45-1 | Threshold Intro | WU 400 + 4×50 drill/swim + 10×100 threshold (15–20s rest) + CD 100 | RPE 6–7 | ~42 |
| THR45-2 | Pace-Change | WU 400 + 6×50 drill/swim + 8×100 as 2 easy/2 moderate/2 threshold/2 moderate + CD 200 | RPE 4–7 | ~41 |
| THR45-3 | Pull Strength | WU 400 + 4×50 drill/swim + 5×100 pull strong + 4×50 fast + CD 200 | RPE 5–7 | ~43 |

---

# 50-minute sessions

Warm-up ~500 m, technique ~400 m, fitness ~1000 m, cool-down ~300 m.

## Technique — 50 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| TECH50-1 | Drill Progression | WU 500 + 10×50 drill/swim + 6×100 aerobic + CD 300 | RPE 2–4 | ~38 |
| TECH50-2 | Rotation & Catch | WU 500 + 8×75 (25 drill/25 kick/25 swim) + 5×100 steady + CD 300 | RPE 2–4 | ~39 |
| TECH50-3 | Mixed Drills | WU 500 + 6×50 catch-up + 6×50 fingertip + 4×100 steady + CD 300 | RPE 2–4 | ~38 |

## Aerobic fitness — 50 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| AER50-1 | Steady 100s | WU 500 + 6×50 drill/swim + 12×100 aerobic (15s rest) + CD 300 | RPE 3–4 | ~42 |
| AER50-2 | Pull Endurance | WU 500 + 6×50 drill/swim + 4×200 pull steady + CD 300 | RPE 3–5 | ~44 |
| AER50-3 | Ladder Endurance | WU 500 + 6×50 drill/swim + 200-300-400-300-200 (20s rest) + CD 300 | RPE 3–5 | ~45 |

## Threshold fitness — 50 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| THR50-1 | Threshold 100s | WU 500 + 6×50 drill/swim + 12×100 threshold (15s rest) + CD 300 | RPE 6–7 | ~48 |
| THR50-2 | Descending 100s | WU 500 + 6×50 drill/swim + 5×100 descend 1–5 + 4×100 threshold + CD 300 | RPE 5–7 | ~47 |
| THR50-3 | Mixed Pace | WU 500 + 6×50 drill/swim + 16×100 as 4 easy/4 moderate/4 threshold/4 moderate + CD 300 | RPE 4–7 | ~46 |

---

# 60-minute sessions

Warm-up ~600 m, technique ~500 m, fitness ~1200 m, cool-down ~300 m.

## Technique — 60 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| TECH60-1 | Technique Base | WU 600 + 12×50 drill/swim + 6×100 aerobic + CD 300 | RPE 2–4 | ~45 |
| TECH60-2 | Single-Arm Series | WU 600 + 8×75 (25 drill/25 kick/25 swim) + 8×100 steady + CD 300 | RPE 2–4 | ~46 |
| TECH60-3 | Feel for Water | WU 600 + 6×100 (25 drill/25 swim/25 drill/25 swim) + 4×25 scull + CD 300 | RPE 2–4 | ~45 |

## Aerobic fitness — 60 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| AER60-1 | Aerobic Base | WU 600 + 12×50 drill/swim + 8×100 aerobic (15–20s rest) + CD 300 | RPE 3–4 | ~50 |
| AER60-2 | Steady Repeats | WU 600 + 12×50 drill/swim + 3×400 steady aerobic (30s rest) + CD 300 | RPE 3–5 | ~52 |
| AER60-3 | Pace-Change Set | WU 600 + 12×50 drill/swim + 16×100 as 4 easy/4 moderate/4 threshold/4 moderate + CD 300 | RPE 3–6 | ~51 |

## Threshold fitness — 60 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| THR60-1 | Threshold 100s | WU 600 + 12×50 drill/swim + 10×100 threshold (15–20s rest) + CD 300 | RPE 6–7 | ~55 |
| THR60-2 | Pull Strength | WU 600 + 12×50 drill/swim + 5×300 pull (25–30s rest) + CD 300 | RPE 5–7 | ~54 |
| THR60-3 | Speed Endurance | WU 600 + 12×50 drill/swim + 8×50 fast controlled (20s rest) + 4×100 threshold + CD 300 | RPE 5–8 | ~56 |

---

# 75-minute sessions

Warm-up ~700 m, technique ~600 m, fitness ~1400 m, cool-down ~300 m.

## Technique — 75 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| TECH75-1 | Long Technique | WU 700 + 12×50 drill/swim + 8×100 steady + CD 300 | RPE 2–4 | ~52 |
| TECH75-2 | Drill Ladder | WU 700 + 8×75 (25 drill/25 kick/25 swim) + 10×100 aerobic + CD 300 | RPE 2–4 | ~53 |
| TECH75-3 | Mixed Skills | WU 700 + 6×100 (25 drill/25 swim/25 drill/25 swim) + 4×25 scull/swim + CD 300 | RPE 2–4 | ~52 |

## Aerobic fitness — 75 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| AER75-1 | Steady Long Repeats | WU 700 + 12×50 drill/swim + 3×400 steady aerobic (30s rest) + CD 300 | RPE 3–5 | ~58 |
| AER75-2 | Ladder Endurance | WU 700 + 10×50 drill/swim + 200-300-400-300-200 + 4×100 strong + CD 300 | RPE 3–5 | ~59 |
| AER75-3 | Pull Endurance | WU 700 + 12×50 drill/swim + 5×300 pull steady + CD 300 | RPE 3–5 | ~57 |

## Threshold fitness — 75 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| THR75-1 | Threshold Blocks | WU 700 + 12×50 drill/swim + 16×100 threshold (15–20s rest) + CD 300 | RPE 6–7 | ~62 |
| THR75-2 | Pace-Change Long | WU 700 + 12×50 drill/swim + 20×100 as 5 easy/5 moderate/5 threshold/5 moderate + CD 300 | RPE 4–7 | ~61 |
| THR75-3 | Strength Endurance | WU 700 + 12×50 drill/swim + 5×300 pull + 8×50 fast + CD 300 | RPE 5–7 | ~63 |

---

# 90-minute sessions

Warm-up ~800 m, technique ~700 m, fitness ~1600 m, cool-down ~400 m.

## Technique — 90 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| TECH90-1 | Technique Endurance | WU 800 + 12×50 drill/swim + 6×100 (25 drill/25 swim/25 drill/25 swim) + CD 400 | RPE 2–4 | ~58 |
| TECH90-2 | Drill Volume | WU 800 + 16×50 drill/swim + 10×100 aerobic + CD 400 | RPE 2–4 | ~59 |
| TECH90-3 | Skills Under Fatigue | WU 800 + 8×75 drill/swim + 12×100 steady + 4×25 scull + CD 400 | RPE 2–4 | ~58 |

## Aerobic fitness — 90 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| AER90-1 | Long Aerobic | WU 800 + 12×50 drill/swim + 16×100 aerobic (15–20s rest) + CD 400 | RPE 3–4 | ~65 |
| AER90-2 | Tri Build | WU 800 + 12×50 build + 2×800 steady (45–60s rest) + 8×50 strong + CD 400 | RPE 3–6 | ~67 |
| AER90-3 | Pull Strength Endurance | WU 800 + 12×50 drill/swim + 5×300 pull + 4×100 strong + CD 400 | RPE 3–5 | ~66 |

## Threshold fitness — 90 min

| ID | Title | Main set | Intensity | TSS |
|----|-------|----------|-----------|-----|
| THR90-1 | Threshold Endurance | WU 800 + 12×50 drill/swim + 16×100 threshold (15–20s rest) + CD 400 | RPE 6–7 | ~72 |
| THR90-2 | Long Pace-Change | WU 800 + 12×50 drill/swim + 24×100 as 6 easy/6 moderate/6 threshold/6 moderate + CD 400 | RPE 4–7 | ~71 |
| THR90-3 | Race-Specific | WU 800 + 12×50 drill/swim + 2×800 negative split + 8×50 strong + CD 400 | RPE 5–7 | ~73 |

---

# Mapping to the planner

| Bank family | `sport` | `purpose_tag` | `is_key_session` | Notes |
|-------------|---------|---------------|------------------|-------|
| Technique (`TECH*`) | `swim` | `economy` | usually `true` | Drill-heavy; technique focus |
| Aerobic fitness (`AER*`) | `swim` | `aerobic_base` | any | Steady aerobic / endurance |
| Threshold fitness (`THR*`) | `swim` | `threshold` | usually `true` | Build/peak quality |

When the planner selects a swim session, it should:

1. Read the week's target **duration** for the swim slot (45 / 50 / 60 / 75 / 90 min) and
   **phase** to choose the family (base → `TECH`/`AER`, build/peak → add `THR`, taper/deload → `TECH`/`AER` only).
2. Pull a workout by ID and expand the main-set shorthand into structured `WorkoutStep`s.
3. **All swim prescriptions must use this bank** — no freeform swim sessions.

---

## Summary counts

- **45 min:** 9 (3 TECH · 3 AER · 3 THR)
- **50 min:** 9 (3 TECH · 3 AER · 3 THR)
- **60 min:** 9 (3 TECH · 3 AER · 3 THR)
- **75 min:** 9 (3 TECH · 3 AER · 3 THR)
- **90 min:** 9 (3 TECH · 3 AER · 3 THR)
- **Total: 45 swimming workouts.**
