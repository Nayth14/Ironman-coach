# Running Workout Bank

A reference library of **63 structured running workouts** for the Ironman coach planner:
**42 interval workouts** (the quality / intensity sessions) and **21 long runs** (the
aerobic endurance sessions). These are the source workouts the planner draws on to fill
the **interval and long-run components of the running portion** of an athlete's plan.

Intensities are expressed as **pace zones** anchored to the athlete's **Threshold pace
(T-pace)** — the running analogue of FTP — so they scale to any athlete. Where pace data
is unknown, use the **RPE / HR equivalents** in the [pace zone reference](#pace-zone-reference).
Easy runs are deliberately **kept out of this bank**: the planner weaves those in as simple
**time-based** easy/recovery runs around these key sessions.

---

## How to use this bank

1. **Pick the session by duration first** (the plan slots a 45 / 60 / 90 min interval run, or
   a 60–150 min long run), then by **purpose** to match the training phase.
2. **Two interval families** (per the brief):
   - **Tempo (`TMP`)** — sustained or cruise-interval work at/around **Threshold (T)** and
     **Marathon (M)** pace. Builds the aerobic ceiling and race-pace durability with low
     orthopedic and recovery cost. The workhorse of triathlon run training.
   - **Fast Intervals (`FI`)** — **VO2max (I)** and **Repetition/speed (R)** work. Sharpens
     top-end aerobic power, running economy, and leg speed. Higher injury/recovery cost — use
     sparingly and build into it.
3. **Two long-run families** (per the brief):
   - **Conversational (Slow Long Run / SLR)** — the *entire* run is genuinely easy (E). Pure
     aerobic base, fat oxidation, and time-on-feet durability.
   - **Race-pace long run** — easy base with **race-pace (RP) efforts** woven in (steady
     blocks, progressive, or fast-finish). Trains pacing, fueling, and fade resistance off
     fatigue.
4. **Phase guidance**
   - **Base:** lean on `TMP` (threshold/cruise) intervals and `SLR` long runs. Introduce a
     little `FI` (short hills, strides, light VO2) for economy without overload.
   - **Build:** add VO2max `FI` work ~once per week; shift long runs toward **race-pace blocks**.
   - **Peak:** sharpen with race-specific `TMP` over-unders and **fast-finish / durability**
     long runs at goal race pace.
5. **Never stack two hard run days back to back, and respect run-specific injury risk.** Most
   triathletes hold **2 quality run sessions per week** (one interval, one long run with or
   without quality), plus easy time-based runs.
6. **Pace ranges scale by athlete and phase** — prescribe the **conservative end early in a
   block** and progress toward the faster end as fitness and durability build.
7. **rTSS is an estimate** (see [load reference](#rtss--load-reference)); actual load scales
   with the athlete's threshold-pace accuracy and how honestly they run recoveries and easy days.

### Research basis

These structures follow established run-training methodology — **Jack Daniels' *Running
Formula* (VDOT E/M/T/I/R zones)**, the lactate-threshold tempo model, and standard
long-course triathlon run construction (Friel, Fitzgerald):

- **Threshold / Tempo (T):** ~"comfortably hard," roughly **1-hour race effort** (RPE 7–8).
  Run as a continuous tempo (≤ ~20–30 min) or **cruise intervals** (5–15 min reps, short jog
  recoveries) to accumulate more time near threshold with less fatigue.
- **Marathon (M):** steady aerobic-strong effort (RPE 5–6); the home of **IM/70.3 run race
  pace** for most age-groupers. Used for race-pace specificity inside tempo and long runs.
- **VO2max / Interval (I):** **3–5 min reps** at ~3K–5K effort (RPE 9), jog recoveries ~50–90%
  of work time. Develops maximal aerobic power.
- **Repetition / Speed (R):** **short reps** (200 m–400 m / 30–60 s) at ~mile–1500 m effort
  (RPE 10 *effort*, not cardiovascular), **full recoveries**. Develops economy and leg speed;
  hill sprints are a low-injury way to get the same stimulus.
- **Long run:** mostly **Easy (E)**, capped at **2.5 h** for the triathlon run (diminishing
  returns and injury risk beyond; bike carries most aerobic volume). Race-pace work goes in the
  **back half**, while pre-fatigued, to build durability.

---

## Pace zone reference

5-zone Daniels/VDOT model, anchored to **Threshold pace (T-pace)**:

| Zone | Name | RPE | % HRmax | Pace anchor | Feel |
|------|------|-----|---------|-------------|------|
| **E** | Easy / Recovery | 2–4 | 65–78% | T-pace **+ 60–90 s/km** slower | Conversational, full sentences, all-day |
| **M** | Marathon / Steady | 5–6 | 79–88% | T-pace **+ 20–40 s/km** slower | Strong but controlled, short sentences |
| **T** | Threshold / Tempo | 7–8 | 88–92% | **T-pace** (≈ 1-hour race effort) | Comfortably hard, a few words only |
| **I** | Interval / VO2max | 9 | 95–100% | T-pace **− 10–20 s/km** faster (≈ 3K–5K) | Very hard, 3–5 min repeatable |
| **R** | Repetition / Speed | 10\* | n/a (effort) | T-pace **− 25–40 s/km** faster (≈ mile) | Fast, smooth, full recovery between reps |

\* R-pace RPE reflects *neuromuscular* effort over short reps, not a maximal cardiovascular
state — these are run **relaxed and fast**, not as all-out sprints.

> **Triathlon run race pace (RP):**
> - **Ironman (140.6):** ~top of **E** / low **M** (RPE 4–5) for most age-groupers.
> - **70.3:** ~**M** to low **T** (RPE 6–7).
> The planner sets RP from the athlete's goal race and uses it inside race-pace long runs and
> race-specific tempo sessions.

**Strides** (referenced in warm-ups): 4–6 × ~20 s relaxed accelerations to ~R effort with full
recovery — they prime fast intervals without adding meaningful fatigue.

---

## rTSS / load reference

`rTSS = duration_hours × IF² × 100`, where `IF = Normalized Graded Pace ÷ Threshold pace`.
One hour at threshold pace = 100 rTSS. Values below are planning estimates assuming the
athlete executes targets and keeps recoveries and easy segments genuinely easy.

| Session family | Typical IF | Typical rTSS |
|----------------|-----------|--------------|
| 45 min intervals | 0.83–0.90 | 55–68 |
| 60 min intervals | 0.83–0.90 | 72–88 |
| 90 min intervals | 0.83–0.90 | 105–125 |
| Long run (Conversational / E) | 0.72–0.76 | ~52–55 / hr |
| Long run (w/ race-pace work) | 0.76–0.82 | ~60–65 / hr |

---

## Index

- [Interval workouts (42)](#interval-workouts)
  - [45-minute (14)](#45-minute-interval-sessions)
  - [60-minute (14)](#60-minute-interval-sessions)
  - [90-minute (14)](#90-minute-interval-sessions)
- [Long runs (21)](#long-run-workouts)
- [Mapping to the planner](#mapping-to-the-planner)

Interval ID scheme: `TMP` tempo/threshold · `FI` fast intervals (VO2/speed), followed by the
duration in minutes and an index (e.g. `TMP45-3`). Long-run IDs use duration in minutes plus a
variant index (e.g. `LR150-2`).

---

# Interval workouts

Each session is **warm-up → main set → cool-down**. Recovery between hard reps is an **easy
jog (E) or walk** as noted. All warm-ups for `FI` sessions finish with **4–6 strides**.

Per duration tier: **7 tempo · 7 fast intervals = 14**.

## 45-minute interval sessions

Warm-up ~12 min easy (+ strides on `FI`), cool-down ~8 min easy, leaving ~25 min for the main set.

### Tempo — 45 min

| ID | Title | Main set (after ~12 min WU, before ~8 min CD) | Pace | rTSS |
|----|-------|-----------------------------------------------|------|------|
| TMP45-1 | Classic Tempo | 20 min continuous | T | ~60 |
| TMP45-2 | Cruise 4 × 5 | 4 × 5 min (60 s jog) | T | ~60 |
| TMP45-3 | Cruise 3 × 7 | 3 × 7 min (90 s jog) | T | ~61 |
| TMP45-4 | Tempo 2 × 10 | 2 × 10 min (2 min jog) | T | ~60 |
| TMP45-5 | Marathon-Tempo | 24 min continuous | M→T | ~57 |
| TMP45-6 | Threshold Cut-Down | 8 → 6 → 4 min (90 s jog) | T | ~60 |
| TMP45-7 | Tempo Floats | 6 × (3 min T / 1 min M) | T / M | ~62 |

### Fast intervals — 45 min

| ID | Title | Main set | Pace | rTSS |
|----|-------|----------|------|------|
| FI45-1 | VO2 5 × 3 | 5 × 3 min (2 min jog) | I | ~60 |
| FI45-2 | VO2 6 × 2 | 6 × 2 min (90 s jog) | I | ~59 |
| FI45-3 | 400s | 8 × 400 m (200 m jog) | I–R | ~58 |
| FI45-4 | 30-30s | 12 × (30 s hard / 30 s easy) | I | ~56 |
| FI45-5 | Hill Reps | 10 × 45 s uphill (jog-down recovery) | R effort | ~57 |
| FI45-6 | VO2 Pyramid | 1-2-3-2-1 min (equal jog) | I | ~58 |
| FI45-7 | Speed + VO2 | 8 × 200 m R (200 jog) + 4 × 1 min I (1 min jog) | R / I | ~59 |

## 60-minute interval sessions

Warm-up ~15 min easy (+ strides on `FI`), cool-down ~10 min easy, leaving ~35 min for the main set.

### Tempo — 60 min

| ID | Title | Main set | Pace | rTSS |
|----|-------|----------|------|------|
| TMP60-1 | Tempo 30 | 30 min continuous | T | ~82 |
| TMP60-2 | Cruise 5 × 6 | 5 × 6 min (60 s jog) | T | ~84 |
| TMP60-3 | Cruise 4 × 8 | 4 × 8 min (90 s jog) | T | ~85 |
| TMP60-4 | Tempo 2 × 15 | 2 × 15 min (3 min jog) | T | ~84 |
| TMP60-5 | Tempo 3 × 10 | 3 × 10 min (2 min jog) | T | ~84 |
| TMP60-6 | Threshold Over-Under | 6 × (4 min T / 1 min M) | T / M | ~86 |
| TMP60-7 | Progressive Tempo | 10 min M → 10 min T → 10 min M (continuous) | M / T | ~82 |

### Fast intervals — 60 min

| ID | Title | Main set | Pace | rTSS |
|----|-------|----------|------|------|
| FI60-1 | VO2 6 × 3 | 6 × 3 min (2 min jog) | I | ~80 |
| FI60-2 | VO2 5 × 4 | 5 × 4 min (2.5 min jog) | I | ~82 |
| FI60-3 | 1K Reps | 5 × 1000 m (2 min jog) | I | ~82 |
| FI60-4 | 400s + 200s | 8 × 400 m (200 jog) + 4 × 200 m (200 jog) | I / R | ~80 |
| FI60-5 | Double 30-30 | 2 × [10 × (30 s / 30 s)] (3 min between sets) | I | ~78 |
| FI60-6 | Long Pyramid | 1-2-3-4-3-2-1 min (equal jog) | I | ~81 |
| FI60-7 | VO2 + Speed | 4 × 3 min I (2 min jog) + 6 × 30 s R (90 s jog) | I / R | ~80 |

## 90-minute interval sessions

Warm-up ~15 min easy (+ strides on `FI`), cool-down ~10 min easy, leaving ~65 min for the main
set — with **easy (E) filler between sets** so the session stays specific without becoming
all-out.

### Tempo — 90 min

| ID | Title | Main set | Pace | rTSS |
|----|-------|----------|------|------|
| TMP90-1 | Long Tempo 2 × 20 | 2 × 20 min (5 min easy) + E fill | T | ~118 |
| TMP90-2 | Tempo 3 × 15 | 3 × 15 min (3 min jog) + E fill | T | ~120 |
| TMP90-3 | Steady State | 40 min continuous + E fill | M→T | ~112 |
| TMP90-4 | Cruise 6 × 8 | 6 × 8 min (2 min jog) + E fill | T | ~122 |
| TMP90-5 | Marathon Simulation | 50 min M with 3 × 5 min T surges | M / T | ~115 |
| TMP90-6 | Over-Under Long | 8 × (4 min T / 2 min M) | T / M | ~120 |
| TMP90-7 | Progressive Thirds | 20 min M → 20 min T → 10 min M + E fill | M / T | ~116 |

### Fast intervals — 90 min

| ID | Title | Main set | Pace | rTSS |
|----|-------|----------|------|------|
| FI90-1 | VO2 8 × 3 | 8 × 3 min (2 min jog) + E fill | I | ~115 |
| FI90-2 | VO2 6 × 4 | 6 × 4 min (3 min jog) + E fill | I | ~117 |
| FI90-3 | 1K + 200s | 6 × 1000 m (2 min jog) + 6 × 200 m R (200 jog) | I / R | ~116 |
| FI90-4 | Double Pyramid | 2 × [1-2-3-2-1 min] (equal jog, 4 min between) + E fill | I | ~114 |
| FI90-5 | 400s + 300s | 10 × 400 m (200 jog) + 5 × 300 m R (300 jog) | I / R | ~115 |
| FI90-6 | Long Fartlek | 25 min of (1 min hard / 1 min easy) inside an easy run | I / E | ~108 |
| FI90-7 | Threshold→VO2 Cut-Down | 4 × 5 min T (90 s jog) then 6 × 2 min I (90 s jog) + E fill | T / I | ~118 |

---

# Long run workouts

21 aerobic endurance runs from **60 min to 150 min (2.5 h) in 15-minute steps** (7 durations ×
3 variants). These build time-on-feet, fat oxidation, and the pacing/fueling durability the
Ironman run leg demands. **Keep the bulk genuinely easy — the most common mistake is letting
the long run drift into Marathon effort.** The triathlon long run is capped at **2.5 h**.

**Every long run:** ~10 min easy build to settle into E, steady aerobic body, ~5–10 min easy
float-down. On hilly courses, let effort (not pace) govern the easy portions.

### Fueling & hydration (apply to all long runs, especially ≥ 90 min)

- **Carbs:** start within ~30 min on runs ≥ 75 min; **40–70 g/hr** from gels/drink, training the
  gut toward **60–90 g/hr** on race-pace sessions.
- **Fluid:** 400–700 ml/hr, small frequent sips; more in heat.
- **Sodium:** 400–800 mg/hr.
- Runs ≥ 2 h are primary **gut-training and fade-resistance** sessions — practice exact race-day
  products and carry/refuel as you will on race day.

### The 3 variants (each duration has one of each)

1. **Conversational (Slow Long Run / SLR)** — pure **Easy (E)** start to finish. Aerobic base,
   fat oxidation, durability. Effort stays conversational the whole way.
2. **Race-Pace Blocks** — easy base with sustained **race-pace (RP)** blocks in the middle/back
   half. Trains pacing discipline and fueling at race effort.
3. **Progressive / Fast Finish** — starts easy and **finishes at race pace (or threshold)** while
   pre-fatigued. Builds fade resistance; heaviest fueling focus.

> RP = goal race pace (IM ≈ top-E/low-M, RPE 4–5; 70.3 ≈ M–low-T, RPE 6–7). rTSS scales with
> duration and the amount of race-pace work; values below are planning estimates.

### 60 min

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR60-1 | Conversational (SLR) | 60 min steady easy | E | ~52 |
| LR60-2 | Race-Pace Blocks | 15 min E + 3 × 8 min RP (3 min E) + E float | E / RP | ~60 |
| LR60-3 | Progressive / Fast Finish | 45 min E → final 15 min building RP → T | E / RP–T | ~58 |

### 75 min

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR75-1 | Conversational (SLR) | 75 min steady easy | E | ~66 |
| LR75-2 | Race-Pace Blocks | 20 min E + 3 × 10 min RP (3 min E) + E float | E / RP | ~76 |
| LR75-3 | Progressive / Fast Finish | 55 min E + final 20 min progressing to T | E / RP–T | ~73 |

### 90 min

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR90-1 | Conversational (SLR) | 90 min steady easy | E | ~80 |
| LR90-2 | Race-Pace Blocks | 25 min E + 4 × 10 min RP (3 min E) + E float | E / RP | ~92 |
| LR90-3 | Progressive / Fast Finish | 65 min E + final 25 min RP (last 5 min @ T) | E / RP–T | ~88 |

### 105 min

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR105-1 | Conversational (SLR) | 105 min steady easy | E | ~93 |
| LR105-2 | Race-Pace Blocks | 30 min E + 3 × 15 min RP (5 min E) + E float | E / RP | ~108 |
| LR105-3 | Progressive Thirds | 35 min E → 35 min M → 35 min RP/T | E / M / RP–T | ~104 |

### 120 min

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR120-1 | Conversational (SLR) | 120 min steady easy | E | ~106 |
| LR120-2 | Race-Pace Blocks | 30 min E + 4 × 15 min RP (5 min E) + E float | E / RP | ~124 |
| LR120-3 | Progressive / Fast Finish | 90 min E + final 30 min RP (last 10 min @ T) | E / RP–T | ~120 |

### 135 min

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR135-1 | Conversational (SLR) | 135 min steady easy | E | ~120 |
| LR135-2 | Race-Pace Blocks | 35 min E + 3 × 20 min RP (5 min E) + E float | E / RP | ~140 |
| LR135-3 | Progressive Thirds | 45 min E → 45 min M → 45 min RP | E / M / RP | ~136 |

### 150 min (2.5 h)

| ID | Variant | Structure | Pace | rTSS |
|----|---------|-----------|------|------|
| LR150-1 | Conversational (SLR) | 150 min steady easy (time-on-feet builder) | E | ~134 |
| LR150-2 | Race Simulation | 40 min E + 4 × 20 min RP (5 min E) + E float (full race fueling) | E / RP | ~156 |
| LR150-3 | Durability Fast Finish | 120 min E + final 30 min RP → T pre-fatigued | E / RP–T | ~150 |

---

# Mapping to the planner

How these workouts map onto the planner's `Workout` / `purpose_tag` model
(`web/src/lib/types.ts`, `coaching-lab/engine/models.py`):

| Bank family | `sport` | `purpose_tag` | `is_key_session` | Notes |
|-------------|---------|---------------|------------------|-------|
| Tempo (`TMP*`) | `run` | `threshold` | `true` | Sustained/cruise T & M work; base→peak workhorse |
| Fast intervals (`FI*`) | `run` | `vo2` (R-heavy → `economy`) | `true` | VO2max & speed; build/peak, used sparingly |
| Long run conversational (`LR*-1`) | `run` | `aerobic_base` | `true` | Pure E; time-on-feet & fat oxidation |
| Long run race-pace / progressive (`LR*-2/-3`) | `run` | `race_execution` (`durability` on the longest) | `true` | Back-half RP = race specificity & fade resistance |
| (Woven-in easy runs — *not* in this bank) | `run` | `recovery` / `aerobic_base` | `false` | Time-based easy/recovery runs the planner adds around key sessions |

When the planner selects the **interval or long-run component of the running portion**, it should:

1. Read the week's target **duration** for the run quality slot (45 / 60 / 90 min interval, or
   60–150 min long run) and the **phase** to choose the family (base → `TMP` / `SLR`,
   build → add `FI` + race-pace long runs, peak → race-specific `TMP` + fast-finish long runs).
2. Pull a workout by ID, scale the **pace zones** to the athlete's current Threshold pace (and
   set `RP` from the goal race), and expand the main-set shorthand into structured
   `WorkoutStep`s (warmup → repeat/work → recovery → cooldown) per
   `coaching-lab/engine/prompts/workout_steps_system.md`. Use `target.type: "rpe"` with the
   zone's RPE band when pace data is unavailable.
3. Carry the **rTSS estimate** into weekly load checks, and avoid scheduling two hard `run`
   sessions within 48 h (per the scheduler's hard-session spacing rules), accounting for run
   injury risk.
4. Fill remaining run volume with **time-based easy runs** (`recovery` / `aerobic_base`), which
   are intentionally not enumerated here.

---

## Summary counts

- **Interval workouts: 42** — 14 × 45 min, 14 × 60 min, 14 × 90 min.
  - Tempo (`TMP`): 21 · Fast intervals (`FI`): 21.
- **Long runs: 21** — 3 each at 60, 75, 90, 105, 120, 135, 150 min.
  - Conversational (SLR): 7 · Race-pace (blocks / progressive / fast-finish): 14.
- **Total: 63 running workouts.**
