# Cycling Workout Bank

A reference library of **100 structured cycling workouts** for the Ironman coach planner:
**60 interval workouts** (the quality / intensity sessions) and **40 long rides** (the
aerobic endurance sessions). These are the source workouts the planner draws on to fill
the **interval session component of the cycling portion** of an athlete's plan.

All intensities are expressed as **% of FTP** (Functional Threshold Power) so they scale to
any athlete. Where an athlete has no power meter, use the RPE/HR equivalents in the
[zone reference](#power-zone-reference).

---

## How to use this bank

1. **Pick the session by duration first** (the plan slots a 45 / 60 / 90 min interval ride),
   then by **purpose** (sweet spot, threshold, or over-under) to match the training phase.
2. **Phase guidance**
   - **Base:** lean on sweet spot (workhorse, repeatable, high stimulus / low fatigue).
   - **Build:** introduce threshold and over-unders ~once per week each.
   - **Peak:** sharpen with shorter, higher threshold work and race-specific over-unders.
3. **Never stack two hard interval days back to back.** Most athletes hold 2 quality
   bike sessions per week, with the long ride as the third key session.
4. **% FTP ranges** give the planner room to scale by Workout Level / athlete experience —
   prescribe the **low end early in a block** and progress toward the high end.
5. **TSS is an estimate** (see [TSS reference](#tss--load-reference)); actual load scales with
   the athlete's FTP accuracy and how they execute recoveries.

### Research basis

These structures follow established protocols from Coggan power-zone training, TrainerRoad,
FasCat (origin of "sweet spot"), and standard Ironman long-ride methodology:

- **Sweet spot:** 88–94% FTP, 10–40 min intervals — best stimulus-to-fatigue ratio, repeatable.
- **Threshold:** 95–105% FTP, 5–20 min intervals — raises FTP, high recovery cost.
- **Over-under:** unders 90–95% FTP / overs 105–110% FTP, 8–16 min blocks — trains lactate
  clearance and surge tolerance near threshold.
- **Long ride:** Zone 2 (65–75% FTP), with optional tempo (76–85%) or Ironman race-pace
  (75–82%) blocks in the back half to build durability. Cap at 6 h (diminishing returns beyond).

---

## Power zone reference

7-zone Coggan model (the model the planner's FTP/zone logic uses):

| Zone | Name | % FTP | RPE | Feel |
|------|------|-------|-----|------|
| Z1 | Active Recovery | < 55% | 1–2 | Very easy spin |
| Z2 | Endurance | 56–75% | 3–4 | Conversational, all-day pace |
| Z3 | Tempo | 76–90% | 5–6 | Comfortably hard, short sentences |
| **SS** | **Sweet Spot** | **88–94%** | **7** | Hard but controlled, sustainable 10–40 min |
| Z4 | Threshold | 91–105% | 8 | Hard, sustainable ~20–40 min total |
| Z5 | VO2max | 106–120% | 9 | Very hard, 3–8 min |
| Z6 | Anaerobic | 121–150% | 10 | All-out, 30 s–2 min |

> **Ironman race pace (IM pace):** ~70–80% FTP for most age-groupers (top of Z2 / low Z3).
> Used inside long rides as the race-specific durability stimulus.

---

## TSS / load reference

`TSS = duration_hours × IF² × 100`, where `IF = Normalized Power ÷ FTP`.
One hour at FTP = 100 TSS. The TSS values below are planning estimates assuming the athlete
executes the prescribed targets and keeps recoveries genuinely easy.

| Session family | Typical IF | Typical TSS |
|----------------|-----------|-------------|
| 45 min intervals | 0.80–0.86 | 48–60 |
| 60 min intervals | 0.83–0.90 | 65–82 |
| 90 min intervals | 0.83–0.90 | 95–120 |
| Long ride (steady Z2) | 0.65–0.70 | 28–33 / hr |
| Long ride (w/ race-pace blocks) | 0.70–0.75 | 33–38 / hr |

---

## Index

- [Interval workouts (60)](#interval-workouts)
  - [45-minute (20)](#45-minute-interval-sessions)
  - [60-minute (20)](#60-minute-interval-sessions)
  - [90-minute (20)](#90-minute-interval-sessions)
- [Long rides (40)](#long-ride-workouts)
- [Mapping to the planner](#mapping-to-the-planner)

Interval ID scheme: `SS` sweet spot · `TH` threshold · `OU` over-under, followed by the
duration in minutes and an index (e.g. `SS45-3`). Long-ride IDs use duration in minutes
(e.g. `LR150-2` = a 2.5 h variant).

---

# Interval workouts

Each session is **warm-up → main set → cool-down**. Recovery valleys between hard intervals
are at **50–55% FTP (Z1)** unless stated. Cadence is **85–95 rpm** unless a low-cadence
("strength"/torque) focus is noted (60–70 rpm).

Per duration tier: **8 sweet spot · 6 threshold · 6 over-under = 20**.

## 45-minute interval sessions

Warm-up ~10 min, cool-down ~5 min, leaving ~30 min for the main set.

### Sweet spot — 45 min

| ID | Title | Main set (after 10 min WU, before 5 min CD) | % FTP | TSS |
|----|-------|---------------------------------------------|-------|-----|
| SS45-1 | Sweet Spot Foundation | 3 × 8 min (3 min easy) | 88–90% | ~50 |
| SS45-2 | Sweet Spot 2 × 12 | 2 × 12 min (6 min easy) | 89–91% | ~52 |
| SS45-3 | Sweet Spot 4 × 6 | 4 × 6 min (2 min easy) | 90–92% | ~51 |
| SS45-4 | Sweet Spot Pyramid | 6 → 8 → 10 min (3 min easy) | 88–92% | ~52 |
| SS45-5 | Sweet Spot Torque | 3 × 9 min @ 60–70 rpm (2 min easy) | 89–91% | ~52 |
| SS45-6 | Sweet Spot Long/Short | 18 min + 10 min (4 min easy) | 88–90% | ~55 |
| SS45-7 | Sweet Spot + Microbursts | 3 × 8 min, 10 s @ 120% every 2 min (3 min easy) | 90% / surges | ~54 |
| SS45-8 | Sweet Spot 2 × 14 | 2 × 14 min (4 min easy) | 88–90% | ~55 |

### Threshold — 45 min

| ID | Title | Main set | % FTP | TSS |
|----|-------|----------|-------|-----|
| TH45-1 | Threshold 4 × 5 | 4 × 5 min (3 min easy) | 98–100% | ~54 |
| TH45-2 | Threshold 3 × 8 | 3 × 8 min (4 min easy) | 98–100% | ~57 |
| TH45-3 | Threshold 2 × 12 | 2 × 12 min (6 min easy) | 96–99% | ~56 |
| TH45-4 | Threshold 5 × 4 | 5 × 4 min (3 min easy) | 102–105% | ~56 |
| TH45-5 | Threshold Descending | 10 → 8 → 6 min (4 min easy) | 98 / 100 / 102% | ~58 |
| TH45-6 | Threshold Race Starts | 6 × 3 min (2 min easy) | 103–105% | ~55 |

### Over-under — 45 min

| ID | Title | Main set (one block = listed pattern) | % FTP under/over | TSS |
|----|-------|----------------------------------------|------------------|-----|
| OU45-1 | O/U 2 × 9 | 2 blocks of [2 min + 1 min] × 3 (5 min easy) | 95% / 105% | ~54 |
| OU45-2 | O/U 3 × 6 | 3 blocks of [2 min + 1 min] × 2 (3 min easy) | 90% / 105% | ~54 |
| OU45-3 | O/U 2 × 12 | 2 blocks of [2 min + 2 min] × 3 (5 min easy) | 95% / 105% | ~57 |
| OU45-4 | O/U Short Surges | 3 blocks of [90 s + 30 s] × 4 (3 min easy) | 93% / 110% | ~56 |
| OU45-5 | O/U 2 × 10 (3/2) | 2 blocks of [3 min + 2 min] × 2 (5 min easy) | 94% / 106% | ~56 |
| OU45-6 | O/U Ladder | [2+1] → [2+2] → [3+2] (4 min easy) | 94% / 106% | ~56 |

## 60-minute interval sessions

Warm-up ~12 min, cool-down ~8 min, leaving ~40 min for the main set.

### Sweet spot — 60 min

| ID | Title | Main set | % FTP | TSS |
|----|-------|----------|-------|-----|
| SS60-1 | Sweet Spot 3 × 10 | 3 × 10 min (4 min easy) | 89–91% | ~68 |
| SS60-2 | Sweet Spot 2 × 20 | 2 × 20 min (8 min easy) — the classic | 88–90% | ~72 |
| SS60-3 | Sweet Spot 4 × 8 | 4 × 8 min (3 min easy) | 90–92% | ~70 |
| SS60-4 | Sweet Spot 3 × 12 | 3 × 12 min (4 min easy) | 89–91% | ~72 |
| SS60-5 | Sweet Spot Torque | 4 × 9 min @ 60–70 rpm (3 min easy) | 89–91% | ~70 |
| SS60-6 | Sweet Spot Pyramid | 8 → 12 → 16 min (4 min easy) | 88–92% | ~71 |
| SS60-7 | Sweet Spot + Surges | 3 × 12 min, 15 s @ 120% every 3 min (4 min easy) | 90% / surges | ~73 |
| SS60-8 | Sweet Spot Over-Distance | 2 × 18 min (6 min easy) | 88–90% | ~72 |

### Threshold — 60 min

| ID | Title | Main set | % FTP | TSS |
|----|-------|----------|-------|-----|
| TH60-1 | Threshold 2 × 20 | 2 × 20 min (10 min easy) — gold standard | 100–105% | ~78 |
| TH60-2 | Threshold 3 × 10 | 3 × 10 min (5 min easy) | 98–102% | ~76 |
| TH60-3 | Threshold 4 × 8 | 4 × 8 min (4 min easy) | 98–100% | ~78 |
| TH60-4 | Threshold 5 × 6 | 5 × 6 min (3 min easy) | 100–103% | ~77 |
| TH60-5 | Threshold Descending | 14 → 12 → 10 min (5 min easy) | 97 / 99 / 101% | ~79 |
| TH60-6 | Threshold 6 × 5 | 6 × 5 min (3 min easy) | 102–105% | ~78 |

### Over-under — 60 min

| ID | Title | Main set | % FTP under/over | TSS |
|----|-------|----------|------------------|-----|
| OU60-1 | O/U 3 × 9 | 3 blocks of [2 min + 1 min] × 3 (5 min easy) | 90% / 105% | ~76 |
| OU60-2 | O/U 3 × 12 (Bear Creek) | 3 blocks of [2 min + 2 min] × 3 (5 min easy) | 95% / 105% | ~79 |
| OU60-3 | O/U 2 × 15 | 2 blocks of [3 min + 2 min] × 3 (6 min easy) | 94% / 106% | ~78 |
| OU60-4 | O/U 4 × 8 | 4 blocks of [3 min + 1 min] × 2 (4 min easy) | 92% / 108% | ~78 |
| OU60-5 | O/U Steep Surges | 3 blocks of [2 min + 1 min] × 3 (4 min easy) | 90% / 110% | ~79 |
| OU60-6 | O/U Pyramid | [2+1]×3 → [2+2]×3 → [3+2]×2 (5 min easy) | 94% / 106% | ~78 |

## 90-minute interval sessions

Warm-up ~15 min, cool-down ~10 min, leaving ~65 min for the main set (with aerobic Z2
filler between sets so the session stays specific without becoming all-out).

### Sweet spot — 90 min

| ID | Title | Main set | % FTP | TSS |
|----|-------|----------|-------|-----|
| SS90-1 | Sweet Spot 3 × 15 | 3 × 15 min (5 min easy) + Z2 fill | 89–91% | ~105 |
| SS90-2 | Sweet Spot 4 × 12 | 4 × 12 min (4 min easy) + Z2 fill | 89–91% | ~108 |
| SS90-3 | Sweet Spot 2 × 25 | 2 × 25 min (8 min easy) + Z2 fill | 88–90% | ~108 |
| SS90-4 | Sweet Spot 3 × 18 | 3 × 18 min (5 min easy) + Z2 fill | 88–90% | ~110 |
| SS90-5 | Sweet Spot Torque | 4 × 12 min @ 60–70 rpm (4 min easy) + Z2 fill | 89–91% | ~106 |
| SS90-6 | Sweet Spot Pyramid | 10 → 15 → 20 → 15 min (4 min easy) + Z2 fill | 88–92% | ~110 |
| SS90-7 | Sweet Spot Tempo Sandwich | 20 min tempo @ 83% → 3 × 10 min SS (3 min easy) | 83% / 90% | ~108 |
| SS90-8 | Sweet Spot Endurance Combo | 60 min Z2 base + 3 × 8 min SS embedded | 70% / 90% | ~100 |

### Threshold — 90 min

| ID | Title | Main set | % FTP | TSS |
|----|-------|----------|-------|-----|
| TH90-1 | Threshold 3 × 15 | 3 × 15 min (6 min easy) + Z2 fill | 98–102% | ~115 |
| TH90-2 | Threshold 4 × 10 | 4 × 10 min (5 min easy) + Z2 fill | 99–102% | ~114 |
| TH90-3 | Threshold 2 × 20 + 1 × 10 | 20 / 20 / 10 min (8 min easy) + Z2 fill | 98–102% | ~118 |
| TH90-4 | Threshold 5 × 8 | 5 × 8 min (4 min easy) + Z2 fill | 100–103% | ~115 |
| TH90-5 | Threshold Descending | 18 → 14 → 10 → 8 min (5 min easy) + Z2 fill | 98–103% | ~117 |
| TH90-6 | Threshold + SS Combo | 2 × 12 min @ 102% + 2 × 15 min @ 90% (5 min easy) | 102% / 90% | ~114 |

### Over-under — 90 min

| ID | Title | Main set | % FTP under/over | TSS |
|----|-------|----------|------------------|-----|
| OU90-1 | O/U 4 × 12 | 4 blocks of [2 min + 2 min] × 3 (5 min easy) + Z2 fill | 95% / 105% | ~116 |
| OU90-2 | O/U 3 × 16 | 3 blocks of [2 min + 2 min] × 4 (6 min easy) + Z2 fill | 95% / 105% | ~118 |
| OU90-3 | O/U 3 × 15 (3/2) | 3 blocks of [3 min + 2 min] × 3 (5 min easy) + Z2 fill | 94% / 106% | ~117 |
| OU90-4 | O/U Race Simulation | 4 blocks of [3 min + 1 min] × 3 (5 min easy) + Z2 fill | 92% / 110% | ~118 |
| OU90-5 | O/U + Threshold Finish | 3 × 12 O/U (2+2) then 1 × 10 @ 102% (5 min easy) | 95/105% then 102% | ~118 |
| OU90-6 | O/U Endurance Combo | 50 min Z2 base + 3 × 12 min O/U (2+2) embedded | 70% / 95% / 105% | ~110 |

---

# Long ride workouts

40 aerobic endurance rides from **2.5 h to 6.0 h in 30-minute steps** (8 durations × 5
variants). These build the saddle time, fat-oxidation, and pacing/fueling durability that
the Ironman bike leg demands. Keep the bulk genuinely easy — **the most common mistake is
letting the long ride drift into Z3.**

**Every long ride:** 10–15 min easy build warm-up, steady aerobic body, 10 min easy
cool-down. Cadence 85–95 rpm. Stay seated and aero where possible to build position-specific
durability.

### Fueling & hydration (apply to all long rides)

- **Carbs:** start within 15–20 min; **60–90 g/hr** (train the gut toward **90–120 g/hr** on
  race-specific rides) from mixed glucose + fructose sources.
- **Fluid:** 500–800 ml/hr, small frequent sips; more in heat.
- **Sodium:** 500–1000 mg/hr.
- Rides ≥ 4 h are primary **gut-training** sessions — practice the exact race-day products.

### The 5 variants (each duration has one of each)

1. **Steady Aerobic** — pure Z2 (65–72% FTP). Pacing discipline + fat oxidation.
2. **Aerobic + Tempo** — Z2 base with **tempo blocks @ 76–85% FTP** in the middle/back third.
3. **Aerobic + IM Race-Pace** — Z2 base with **race-pace blocks @ 75–82% FTP** in the second half.
4. **Progressive (Negative Split)** — intensity steps up by thirds, finishing at the high end of Z2 / low Z3.
5. **Durability / Fade-Resistance** — easy Z2 then **race-pace work in the final hour** while
   pre-fatigued; heaviest fueling focus.

> TSS scales with duration and the amount of tempo/race-pace work. Values below are planning estimates.

### 2.5 h (150 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR150-1 | Steady Aerobic | Continuous steady | 65–72% | ~118 |
| LR150-2 | Aerobic + Tempo | Z2 + 2 × 15 min tempo | 70% / 80–85% | ~128 |
| LR150-3 | Aerobic + IM Race-Pace | Z2 + 2 × 20 min race-pace | 70% / 75–82% | ~130 |
| LR150-4 | Progressive | 50 min @ 65% → 50 min @ 70% → 50 min @ 75% | 65→75% | ~126 |
| LR150-5 | Durability Finish | 90 min Z2 + final 45 min as 3 × 12 min race-pace | 70% / 78–82% | ~135 |

### 3.0 h (180 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR180-1 | Steady Aerobic | Continuous steady | 65–72% | ~140 |
| LR180-2 | Aerobic + Tempo | Z2 + 2 × 20 min tempo | 70% / 80–85% | ~152 |
| LR180-3 | Aerobic + IM Race-Pace | Z2 + 3 × 20 min race-pace | 70% / 75–82% | ~158 |
| LR180-4 | Progressive | 60 min @ 65% → 60 min @ 70% → 60 min @ 75% | 65→75% | ~150 |
| LR180-5 | Durability Finish | 2 h Z2 + final hour as 3 × 15 min race-pace | 70% / 78–82% | ~162 |

### 3.5 h (210 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR210-1 | Steady Aerobic | Continuous steady | 65–72% | ~165 |
| LR210-2 | Aerobic + Tempo | Z2 + 3 × 20 min tempo | 70% / 80–85% | ~182 |
| LR210-3 | Aerobic + IM Race-Pace | Z2 + 3 × 25 min race-pace | 70% / 75–82% | ~188 |
| LR210-4 | Progressive | 70 min @ 65% → 70 min @ 70% → 70 min @ 76% | 65→76% | ~176 |
| LR210-5 | Durability Finish | 2.5 h Z2 + final hour as 4 × 12 min race-pace | 70% / 78–82% | ~190 |

### 4.0 h (240 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR240-1 | Steady Aerobic | Continuous steady | 65–72% | ~188 |
| LR240-2 | Aerobic + Tempo | Z2 + 3 × 20 min tempo | 70% / 80–85% | ~205 |
| LR240-3 | Aerobic + IM Race-Pace | Z2 + 4 × 25 min race-pace | 70% / 75–82% | ~218 |
| LR240-4 | Progressive | 80 min @ 65% → 80 min @ 70% → 80 min @ 76% | 65→76% | ~200 |
| LR240-5 | Durability Finish | 3 h Z2 + final hour as 3 × 18 min race-pace | 70% / 78–82% | ~222 |

### 4.5 h (270 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR270-1 | Steady Aerobic | Continuous steady | 65–72% | ~210 |
| LR270-2 | Aerobic + Tempo | Z2 + 4 × 20 min tempo | 70% / 80–85% | ~232 |
| LR270-3 | Aerobic + IM Race-Pace | Z2 + 4 × 30 min race-pace | 70% / 75–82% | ~245 |
| LR270-4 | Progressive | 90 min @ 65% → 90 min @ 70% → 90 min @ 76% | 65→76% | ~225 |
| LR270-5 | Durability Finish | 3.5 h Z2 + final hour as 4 × 14 min race-pace | 70% / 78–82% | ~250 |

### 5.0 h (300 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR300-1 | Steady Aerobic | Continuous steady | 65–72% | ~235 |
| LR300-2 | Aerobic + Tempo | Z2 + 4 × 20 min tempo | 70% / 80–85% | ~258 |
| LR300-3 | Aerobic + IM Race-Pace | Z2 + 4 × 30 min race-pace | 70% / 75–82% | ~272 |
| LR300-4 | Progressive | 100 min @ 65% → 100 min @ 70% → 100 min @ 78% | 65→78% | ~250 |
| LR300-5 | Durability Finish | 4 h Z2 + final hour as 3 × 18 min race-pace | 70% / 78–82% | ~278 |

### 5.5 h (330 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR330-1 | Steady Aerobic | Continuous steady | 65–72% | ~258 |
| LR330-2 | Aerobic + Tempo | Z2 + 5 × 20 min tempo | 70% / 80–85% | ~282 |
| LR330-3 | Aerobic + IM Race-Pace | Z2 + 5 × 30 min race-pace | 70% / 75–82% | ~298 |
| LR330-4 | Progressive | 110 min @ 65% → 110 min @ 70% → 110 min @ 78% | 65→78% | ~275 |
| LR330-5 | Durability Finish | 4.5 h Z2 + final hour as 4 × 14 min race-pace | 70% / 78–82% | ~305 |

### 6.0 h (360 min)

| ID | Variant | Structure | % FTP | TSS |
|----|---------|-----------|-------|-----|
| LR360-1 | Steady Aerobic | Continuous steady (saddle-time builder) | 65–70% | ~280 |
| LR360-2 | Aerobic + Tempo | Z2 + 5 × 20 min tempo | 70% / 80–85% | ~305 |
| LR360-3 | Aerobic + IM Race-Pace | Z2 + 5 × 30 min race-pace | 70% / 75–82% | ~322 |
| LR360-4 | Progressive | 2 h @ 65% → 2 h @ 70% → 2 h @ 76% | 65→76% | ~300 |
| LR360-5 | Race Simulation | 5 h Z2 + final hour as 3 × 20 min race-pace (full race fueling) | 70% / 78–82% | ~330 |

---

# Mapping to the planner

How these workouts map onto the planner's `Workout` / `purpose_tag` model
(`web/src/lib/types.ts`, `coaching-lab/engine/models.py`):

| Bank family | `sport` | `purpose_tag` | `is_key_session` | Notes |
|-------------|---------|---------------|------------------|-------|
| Sweet spot (`SS*`) | `bike` | `threshold` | usually `true` | Sub-threshold quality; base workhorse |
| Threshold (`TH*`) | `bike` | `threshold` | `true` | True FTP work; build/peak |
| Over-under (`OU*`) | `bike` | `threshold` | `true` | Lactate clearance; build/peak |
| Long ride steady/progressive (`LR*-1/-4`) | `bike` | `aerobic_base` | `true` | Z2 durability |
| Long ride tempo/race-pace (`LR*-2/-3/-5`) | `bike` | `durability` / `race_execution` | `true` | Back-half intensity = race specificity |

When the planner selects the **interval session component of the cycling portion**, it should:

1. Read the week's target **duration** for the bike quality slot (45 / 60 / 90 min) and the
   **phase** to choose the family (base → `SS`, build → `TH`/`OU`, peak → sharper `TH`/`OU`).
2. Pull a workout by ID, scale the **% FTP** targets to the athlete's current FTP, and expand
   the main-set shorthand into structured `WorkoutStep`s (warmup → repeat/work → recovery →
   cooldown) per `coaching-lab/engine/prompts/workout_steps_system.md`.
3. Carry the **TSS estimate** into weekly load checks, and avoid scheduling two `threshold`
   bike sessions within 48 h (per the scheduler's hard-session spacing rules).

---

## Summary counts

- **Interval workouts: 60** — 20 × 45 min, 20 × 60 min, 20 × 90 min.
  - Sweet spot: 24 · Threshold: 18 · Over-under: 18.
- **Long rides: 40** — 5 each at 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0 h.
- **Total: 100 cycling workouts.**
