# Adaptation Playbook — Nayth's Ironman Coach

- **Version:** 1.0
- **Date:** 2026-06-15
- **Status:** Engineering Spec (implementation source of truth)
- **Audience:** Engineers (rule engine, mutators, tests) + the LLM narrator
- **Related:** `docs/adaptions/PRD-Fully-Adaptable-Planning.md`, `docs/adaptions/ADR-001-Fully-Adaptable-Planning.md`, `coaching-lab/engine/adaptation/`

> **How to read this document.** Every rule is tagged `[ENGINE]` (deterministic code, must be unit-tested) or `[NARRATOR]` (LLM explanation only — never decides load). `[OPEN QUESTION]` marks where reasonable coaches disagree; each carries a recommended default that engineers should implement now. Recommendations cite the guardrail (`GR-*`), principle (`P1–P6`), or unplanned-recovery rule (`PER-050`) they serve.

### Reference codes used throughout

| Code | Meaning |
|------|---------|
| **P1** | Durability first — 75–85% easy; progressive long sessions |
| **P2** | Race-specific periodization (Prep→Base→Build→Peak→Taper, built backward) |
| **P3** | Four pillars integrated (S/B/R + strength, fueling, recovery) |
| **P4** | Bike durability central; conservative run; frequent swim technique |
| **P5** | Adaptive weekly loop — explicit progress/hold/deload |
| **P6** | Conservative bias — when uncertain, do not progress |
| **GR-VOL10** | Max weekly volume increase 10% |
| **GR-DEL50** | Max deload reduction 50% |
| **GR-EASY80** | ≥80% easy when volume >7h; mandatory above 15h/week |
| **GR-DEL35** | Scheduled deload ≈35% reduction; 3:1 microcycle (every 4th week) |
| **GR-DELFREQ** | Deload keeps session frequency; cuts duration |
| **GR-NOHARD2** | No consecutive hard run days |
| **GR-LR3** | Max 3 standalone long runs (≥90 min) per rolling 4-week block (outside taper) |
| **GR-BIKE50** | Bike ≈50% of endurance volume; run 2–3×/wk; no marathon-distance training runs |
| **PER-050** | Adaptation may insert an unplanned 3–5 day recovery when accumulated fatigue demands it |

---

## 1. Purpose & scope

**What adaptation IS.** A deterministic weekly correction layer that converts recent athlete feedback into (a) concrete mutations of materialized workouts and (b) updates to long-term `PlanState` trajectory. It answers one question every review cycle: *given how the athlete actually responded, do we progress, hold, deload, or reroute load?* `[ENGINE]`

**What adaptation IS NOT.**
- It is **not** macro plan design. Phase boundaries, race date, and the Prep→Base→Build→Peak→Taper skeleton are owned by the periodization engine (`P2`). Adaptation can *nudge* trajectory (slow ramp, pull recovery forward, extend Base) but never redraws the macro plan from scratch. `[ENGINE]`
- It is **not** an LLM judgement. The narrator explains; it never selects a decision or a load number (`P5`, PRD §4 Non-Goals). `[NARRATOR]`
- It is **not** a motivational nudge. "Recovery is a feature, not a failure" — a deload is a success state, not a penalty. `[NARRATOR]`

**Micro vs macro.**
- **Micro (weekly):** the 7-day decision that mutates the next 1–2 materialized weeks.
- **Macro (block):** changes to `PlanState` that alter how *future* weeks are generated (only ~4 weeks are materialized at a time; the rest are computed from state).

**Scheduled deload (3:1) vs unplanned recovery (PER-050).**

| | Scheduled deload (`GR-DEL35`) | Unplanned recovery (`PER-050`) |
|---|---|---|
| Trigger | Calendar — every 4th week | Signal — stacked fatigue mid-block |
| Size | ≈35% volume cut | 30–50% cut, 3–5 days |
| Owner | Periodization engine | Adaptation engine (`deload` decision) |
| Interaction | If a deload signal lands **in** a scheduled deload week, do **not** double-cut (see §5.9) | Resets the 3:1 clock; the next scheduled deload may be pushed if recovery already banked |

[ENGINE] The engine must always know "weeks since last recovery" so it never stacks a PER-050 deload immediately before a scheduled one.

---

## 2. Signal aggregation `[ENGINE]`

Signals are evaluated over three nested windows. The 7-day window decides; the 14- and 28-day windows *gate and modify* that decision.

### 2.1 Windows

| Window | Role | Primary use |
|--------|------|-------------|
| **7-day** | Immediate decision | progress/hold/deload/route selection |
| **14-day** | Trend confirmation | block a progress that follows a hold; confirm a real downtrend |
| **28-day / block** | Macro trajectory | ramp-rate, forced deloads, run-cap, phase extension |

### 2.2 Warning flags (refined baseline)

A "warning flag" is counted once per condition per 7-day window:

1. RPE ≥ 8 on **2+** sessions.
2. Readiness ≤ 4 on **2+** sessions.
3. Any fatigue flag reported (musculoskeletal, GI, life-stress, sleep).
4. Any missed session.

**Refinement (with justification):** the baseline treats *any single* fatigue flag as a flag. Keep that — but **weight a missed _key_ session as 2 flags** and a missed *optional* session as 0.5 (rounded down only at the decision boundary). Rationale: missing the key long ride is materially different from skipping an optional second swim (`P4`, `GR-BIKE50`). `[OPEN QUESTION]` Some coaches treat all misses equally for simplicity. **Default: weight key misses heavier** — it protects the sessions that drive Ironman durability.

### 2.3 Aggregation rules

1. **Minimum sessions to evaluate progress.** Require **≥3 completed sessions** in the 7-day window AND **≥1 completed key session**. Below that → `hold (insufficient data)` (`P6`). `[ENGINE]`
2. **All-green streak before progress.** Progress requires the current week green **and** no warning flag in the prior 7 days (i.e. 14-day clean). Prevents progressing the week immediately after a hold. `[ENGINE]`
3. **Consecutive holds.** 2 consecutive hold weeks → escalate to macro action (pull deload forward — §6). `[ENGINE]`
4. **Consecutive deloads.** 2 deloads inside one 28-day block → freeze progression for 2 weeks and flag for phase extension; never auto-progress out of back-to-back deloads. `[ENGINE]`
5. **Partial weeks.** If the window covers <5 planned sessions (e.g. travel week, plan start, mid-onboarding), treat as partial: progress is disabled; only hold/deload/route decisions allowed. `[ENGINE]`
6. **Trend confirmation.** A single low-readiness day inside an otherwise green 14-day window does not downgrade a hold to deload; deload needs the flags to *cluster* (§4.3). `[ENGINE]`

---

## 3. Session priority hierarchy `[ENGINE]`

When trimming (Hold) or cutting (Deload), preserve in this order. **Rank 1 = most protected.**

| Rank | Session class | Hold (10–20% trim) | Deload (30–50% cut) | Progress |
|------|---------------|--------------------|--------------------|----------|
| 1 | **Key long ride** (durability anchor, `P4`) | Keep; trim ≤10% duration only | Keep session; cut duration ≤35%, drop intensity | First to extend |
| 2 | **Key long run** (≥90 min, `GR-LR3`) | Keep; trim ≤15% | Keep but cap duration; convert surges to easy | Extend only if run-cap allows |
| 3 | **Race-sim brick** | Keep if in Build/Peak; else trim to base | Convert to easy ride + short run off bike | Add only in Build/Peak |
| 4 | **Limiter-discipline quality** (athlete's weakest sport) | Keep 1 quality block; trim secondary | Strip intensity tags; keep aerobic shell | Density target |
| 5 | **Threshold / VO2 quality** | Reduce reps ~20% | Remove intensity entirely (`strip_intensity_tags`) | Density target |
| 6 | **Technique swims** (`P4` frequent technique) | Keep frequency; shorten | Keep ≥1; shorten | Maintain frequency |
| 7 | **Strength** | Keep 1× maintenance; drop 2nd | Drop heavy/eccentric; keep mobility (see note) | Keep 2×, progress slowly |
| 8 | **Easy aerobic filler** | First to trim | Cut hardest here (protects 80/20, `GR-EASY80`) | Add volume here first |
| 9 | **Optional second sessions** | Remove first (`remove_optional_session`) | Remove entirely | Add last |

**Strength note `[ENGINE]`:** On deload, cut **heavy/eccentric loading** (it adds recovery cost) but **keep light mobility/activation** — it aids recovery (`P3`). Never delete strength entirely during an injury/bike-substitute route; it's protective.

**Trim-order principle:** always trim from the bottom up (Rank 9 → Rank 1). Easy filler and optional sessions absorb cuts before any key session is touched (`P1`, `P5`).

---

## 4. Decision playbooks

Mutation op vocabulary (engineers implement these): `scale_non_key_duration(factor)`, `scale_week_volume(factor)`, `remove_optional_session()`, `replace_workout(run→bike_endurance)`, `strip_intensity_tags()`, `force_deload_week()`, `insert_recovery_block(days)`, `modify_fueling_notes()`, `freeze_progression_rate(weeks)`, `pull_deload_forward(weeks)`, `set_run_volume_cap(factor)`, `set_gut_training_mode(bool)`.

### 4.1 `progress`

**A. Entry criteria.** All planned sessions completed; all RPE < 8; zero warning flags; ≥3 completed incl. ≥1 key; 14-day clean (§2.3). `[ENGINE]`
**B. Allowed mutations (ordered).**
1. `scale_week_volume(≤1.10)` (`GR-VOL10`) **OR** density increase — never both same week (§7).
2. Add volume at Rank 8 (easy aerobic) first; extend key long ride (Rank 1) second.
3. Advance progression_rate one notch if 2+ consecutive greens.
**C. Forbidden.** No volume + density same week; never exceed `GR-VOL10`; never add a 4th standalone long run inside the rolling block (`GR-LR3`); never break `GR-EASY80`. `[ENGINE]`
**D. Phase modifiers.** Prep/Base: progress **volume**. Build: progress **density/intensity**, hold volume flat. Peak: tiny volume, sharpen quality. Taper: **never progress volume** (§5.10).
**E. Experience.** Beginner: cap effective progress at +5% even though `GR-VOL10` allows 10%. Intermediate: up to +8%. Advanced: up to +10%. `[OPEN QUESTION]` default to these sub-caps; they encode `P6` for less durable athletes.
**F. Injury modifier.** If `injury_flags` present → progress is **disabled**; downgrade to hold until 2 clean weeks.
**G. Worked example.** Intermediate, Base wk 6, 9.0h, all green. → `scale_week_volume(1.08)` → 9.7h; add 25 min to easy ride and 10 min to long run; long ride 3:30→3:40. Quality sessions unchanged. Easy share recomputed ≥80%.

### 4.2 `hold`

**A. Entry criteria.** 1–2 warning flags, no orthopedic/GI route triggered. `[ENGINE]`
**B. Allowed mutations (ordered).**
1. `scale_non_key_duration(0.80–0.90)` (10–20% trim, Ranks 8–9 first).
2. `remove_optional_session()` if ≥2 flags.
3. `freeze_progression_rate(1)` — no ramp next week.
4. Keep all key sessions intact.
**C. Forbidden.** Never cut key sessions; never increase volume; never strip key intensity unless the flag is intensity-driven. `[ENGINE]`
**D. Phase modifiers.** Build/Peak: protect quality, trim easy. Taper: hold is the *ceiling* decision (§5.10).
**E. Experience.** Beginner: trim 20% (closer to deload-lite). Advanced: trim 10%.
**F. Injury modifier.** Any musculoskeletal flag escalates toward §4.4 routing, not plain hold.
**G. Worked example.** Easy run RPE 8 + "poor sleep" (2 flags, no MSK pain). → hold: `scale_non_key_duration(0.85)`, remove optional 2nd swim, `freeze_progression_rate(1)`. Long ride + key run preserved. (Matches the screenshot case — see §5.1.)

### 4.3 `deload`

**A. Entry criteria.** ≥3 warning flags in 7-day window (with key-miss weighting, §2.2), OR 2 consecutive holds escalating, OR PER-050 accumulated-fatigue trigger. `[ENGINE]`
**B. Allowed mutations (ordered).**
1. `scale_week_volume(0.50–0.70)` → 30–50% cut (`GR-DEL50`), reconciled to ≈35% default (§7).
2. `strip_intensity_tags()` across the week (keep easy aerobic).
3. `insert_recovery_block(3–5 days)` if PER-050.
4. **Preserve session frequency, cut duration** (`GR-DELFREQ`).
5. `pull_deload_forward()` / reset 3:1 clock.
**C. Forbidden.** Never drop below frequency floor; never remove all easy movement (full rest only if illness, §5.5); never deload + a scheduled deload in the same week (§5.9). `[ENGINE]`
**D. Phase modifiers.** Build/Peak deload protects the *next* key block — cut intensity hardest. Taper: a "deload" during taper is just confirming the taper, not an extra cut (§5.10).
**E. Experience.** Beginner: lean to full recovery week (50% cut). Advanced: 30–35% may suffice.
**F. Injury modifier.** If MSK-driven, combine with run-cap (§4.4).
**G. Worked example.** Build wk 3, 11h, RPE≥8 ×3 + readiness≤4 ×2 + "heavy legs". → `scale_week_volume(0.65)` → 7.2h; strip all VO2/threshold tags; keep 5 sessions at reduced duration; `pull_deload_forward()`. Long ride kept at 2:30 easy.

### 4.4 `bike_substitute`

**A. Entry criteria.** Run orthopedic keyword (knee/shin/calf/achilles/foot/hip) on a **run** session, or matching `profile.injury_flags`. 1 session = niggle handling (§5.7); 2+ sessions = chronic route. `[ENGINE]`
**B. Allowed mutations (ordered).**
1. `replace_workout(run→bike_endurance)` for the offending/secondary run (keep heart-rate-equivalent aerobic load).
2. `set_run_volume_cap(0.6–0.8)` in `PlanState`.
3. Preserve run **frequency** where pain-free; reduce **load**.
4. Keep technique swims + long ride (bike absorbs displaced volume, `GR-BIKE50`, `P4`).
**C. Forbidden.** Never add intensity to the substitute bike (it's endurance replacement); never remove all running unless pain on walking (then → §5.5 medical). Never exceed bike share that breaks brick specificity in Peak without flagging. `[ENGINE]`
**D. Phase modifiers.** Base: easy to substitute freely. Build/Peak: preserve at least one run-off-bike for race specificity even while capping volume.
**E. Experience.** Beginner: cap run harder (0.6). Advanced w/ history: 0.8.
**F. Injury modifier.** This *is* the injury route; `set_run_volume_cap` persists ≥2 weeks, lifted only after 2 pain-free weeks.
**G. Worked example.** "Left knee" on Tue easy run. → replace Tue run with 45-min easy bike; long run kept but capped; `set_run_volume_cap(0.7)`; add knee-friendly mobility to strength. Run frequency 3→2.

### 4.5 `gut_training`

**A. Entry criteria.** GI/stomach/gut/nausea/cramp keyword on any session. Long-ride-only vs all-sessions changes scope (§5.8). `[ENGINE]`
**B. Allowed mutations (ordered).**
1. `set_gut_training_mode(true)` in `PlanState`.
2. `modify_fueling_notes()`: step carbohydrate target **down**, then ramp gradually; simplify product mix.
3. Rehearse fueling specifically in the long ride (`fueling` purpose_tag).
4. Hold global volume — do **not** progress load while gut is unstable (`P6`).
**C. Forbidden.** Never treat GI as a generic deload (don't cut training volume reflexively); never raise carb target while symptomatic; never add intensity that masks GI tolerance. `[ENGINE]`
**D. Phase modifiers.** Base: build tolerance early. Peak: lock the rehearsed race-day intake; no experimentation. Taper: fueling rehearsal only at race-day numbers, low volume.
**E. Experience.** Beginner: start lower carb floor; longer ramp. Advanced: shorter ramp.
**F. Injury modifier.** Independent of MSK; can co-exist with bike_substitute (apply both routes).
**G. Worked example.** "Nausea" on 4h long ride. → `set_gut_training_mode`; fueling note drops 90→60 g/h then +5 g/h weekly; product simplified to one drink mix; volume held flat; no deload.

---

## 5. Specialized scenarios

### 5.1 High RPE on an "easy" session (screenshot case) `[ENGINE]`
Easy run RPE 8 + "poor sleep" = 2 flags, no MSK keyword. → **`hold`, not deload.** Trim non-key 15%, remove an optional session, freeze progression 1 week. Deload only if a *third* flag joins. Rationale: one hard-feeling easy day with poor sleep is acute, not accumulated (`P6`, §2.3 trend rule). `[NARRATOR]` reassure: an off day ≠ failure.

### 5.2 Missed key vs missed optional `[ENGINE]`
- Missed **key** session = weighted 2 flags → typically lands in hold, and if combined with any other flag → deload candidate. Reschedule the key session before adding anything new.
- Missed **optional** = 0.5 weight → usually no decision change. Drop it; don't backfill.

### 5.3 Missed long ride or long run `[ENGINE]`
Never "make up" a missed long session by stacking it on an adjacent day (`GR-NOHARD2`, 48h separation). Options in priority: (1) shift it to the week's open long-session slot if ≥48h from the other long session; (2) if no safe slot, **forfeit this week's progression** and re-anchor next week. Two consecutive missed long rides → macro flag: extend Base / slow ramp (§6).

### 5.4 Life stress / poor sleep, no MSK pain `[ENGINE]`
Treat as fatigue flags feeding hold/deload by count — **not** bike_substitute (no orthopedic route). Sleep debt is a systemic stressor: 1–2 flags → hold; persistent across 14 days → PER-050 recovery block even without RPE spikes. `[NARRATOR]` prescribe sleep as the week's "key session."

### 5.5 Returning from illness (3+ days off) `[ENGINE]`
Override ladder. Re-entry protocol: Week 1 back = 50% volume, **zero intensity**, frequency restored gradually, no key long session at full duration. Progress disabled for 1 full week minimum; require 1 clean week before normal evaluation. Full rest is permitted here (the one case overriding "keep easy movement"). Serves `P6`.

### 5.6 (Reserved — see §5.7/§5.8 for niggle/gut granularity.)

### 5.7 Run niggle (1 session) vs chronic stress (2+) `[ENGINE]`
- **1 session:** "niggle handling" — soften, don't reroute the whole block. Replace *that one* run with bike or easy alternative; monitor; do **not** set a long run-cap yet.
- **2+ sessions** (within 14 days): chronic → full `bike_substitute` route + `set_run_volume_cap` persisted ≥2 weeks (§4.4).

### 5.8 Gut issues: long ride only vs all sessions `[ENGINE]`
- **Long ride only:** scoped gut_training on fueling sessions; likely intake-rate/product issue. Keep rest of plan normal.
- **All sessions:** systemic — gut_training mode + hold global volume + check for illness overlap (§5.5). Lower carb floor more aggressively.

### 5.9 Deload week coinciding with unplanned deload signals `[ENGINE]`
If the current week is already a **scheduled** deload (`GR-DEL35`) and signals also call for deload: **do not double-cut.** Honor the deeper of the two (cap at `GR-DEL50`), extend recovery by 1–2 days if PER-050 fires, and `pull_deload_forward` is a no-op (already deloading). Reset block counters afterward.

### 5.10 Adaptation during Taper `[ENGINE]`
Taper is descending by design. Rules: **never progress volume**; amber signals → `hold` only (maintain the planned taper shape); red/stacked signals → trim intensity, **not** the few sharpening efforts that keep neuromuscular readiness. Keep frequency and race-pace touches; cut duration. `[NARRATOR]` frame fatigue in taper as normal "taper tantrums."

### 5.11 Progress during Build vs Base `[ENGINE]`
- **Base:** progress = **volume** (`scale_week_volume ≤1.10`), aerobic filler first.
- **Build:** progress = **density/intensity** (more quality, sharper key sessions); keep volume roughly flat. Never raise volume *and* intensity together (§7).

### 5.12 Two consecutive Hold weeks → macro action `[ENGINE]`
2 holds = the plan is asking for recovery it isn't getting. → `pull_deload_forward(1)`, slow progression_rate one notch, log to 28-day trajectory. See §6.

---

## 6. Macro trajectory rules `[ENGINE]`

`PlanState` (persisted per active plan; future weeks generated from it):

| Variable | Type | Updated by |
|----------|------|-----------|
| `volume_multiplier` | float (cap 1.10/wk) | progress/hold/deload |
| `progression_rate` | enum {frozen, slow, normal} | holds, deloads, greens |
| `forced_deload_weeks` | list[int] | `pull_deload_forward`, PER-050 |
| `run_volume_cap` | float (0–1) | bike_substitute, niggles |
| `gut_training_mode` | bool | gut_training |
| `consecutive_holds` | int | hold/clear |
| `consecutive_deloads` | int | deload/clear |
| `weeks_since_recovery` | int | every week tick |
| `decision_history` | list | every evaluation |

**Rules:**
1. **Slow the ramp.** Each hold drops `progression_rate` one notch (normal→slow→frozen). Each clean week recovers one notch (max normal). `[ENGINE]`
2. **Extend Base.** 2 deloads or 3 holds inside Base → push Build start +1 week (`P2` built-backward preserved by compressing nothing past the race date; if no room, cap Build volume instead). `[ENGINE]` `[OPEN QUESTION]` whether to shift phase boundaries automatically in v1 — **default: yes, but only ±1 week and only into Base/Build, never into Taper.**
3. **Delay Build intensity.** If `consecutive_holds ≥2` at Base→Build transition, keep aerobic emphasis 1 extra week before adding threshold/VO2. `[ENGINE]`
4. **Pull recovery forward.** 2 holds or PER-050 → insert `forced_deload_weeks` at the next available week. `[ENGINE]`
5. **Cap peak volume after repeated amber.** ≥3 amber (hold/deload) weeks in the trailing 28-day block → cap Peak `volume_multiplier` at the trailing 4-week average, never the planned peak. Protects against ramping into the race on a fragile base (`P1`, `P6`). `[ENGINE]`
6. **Run-cap lifecycle.** `run_volume_cap` <1.0 persists until 2 pain-free weeks, then steps back to 1.0 by +0.1/week (no jump). `[ENGINE]`

---

## 7. Progression math `[ENGINE]`

**Definitions.**
- **Volume** = total weekly endurance hours.
- **Density** = quality work per week (number/length of threshold/VO2/race-pace intervals, or key-session frequency) at roughly constant volume.

**Next-week target on Progress.**
```
raw = current_hours * (1 + base_step)
target = min(raw, current_hours * (1 + 0.10))      # GR-VOL10 hard cap
```
where `base_step` = experience sub-cap (beginner 0.05, intermediate 0.08, advanced 0.10) × phase factor (Base 1.0, Build 0.3, Peak 0.1, Taper 0.0). Round to nearest 5 min/session. Re-validate `GR-EASY80` after.

**Trim factor on Hold.**
```
trim = 0.10 if flags == 1 else 0.20            # applied to non-key duration only
non_key_hours *= (1 - trim)
key_hours unchanged
```

**Deload factor (reconciling 35% vs 30–50%).**
```
default_deload = 0.35                            # GR-DEL35 scheduled shape
if PER-050 severity high: deload up to 0.50      # GR-DEL50 ceiling
factor = clamp(deload, 0.30, 0.50)
target = current_hours * (1 - factor)
frequency preserved (GR-DELFREQ); duration absorbs the cut
```
Default unplanned deload uses **0.35** to match the scheduled shape unless severity (≥4 flags, or readiness ≤3 repeatedly) pushes toward 0.50.

**Volume OR density — never both.** `[ENGINE]` In any single week a Progress decision may raise volume **or** density, not both. Phase decides which (§5.11). Enforce with a guard that rejects a mutation set containing both `scale_week_volume>1.0` and an intensity/density increase.

---

## 8. Validation checklist `[ENGINE]`

After **every** mutation set, assert (reject + fall back to safest valid `hold` profile on failure, per PRD §8.5):

1. **80/20 compliance.** Easy share ≥80% when volume >7h; mandatory above 15h (`GR-EASY80`).
2. **Volume caps.** Week-over-week increase ≤10% (`GR-VOL10`); deload reduction ≤50% (`GR-DEL50`).
3. **Scheduling gaps.** No consecutive hard run days (`GR-NOHARD2`); ≥48h between the two long sessions (long bike / long run separation).
4. **Deload shape.** Frequency preserved; cut came from duration, not session count (`GR-DELFREQ`).
5. **Long-session caps.** ≤3 standalone long runs ≥90 min per rolling 4-week block outside taper (`GR-LR3`); no marathon-distance training run (`GR-BIKE50`).
6. **Discipline balance.** Bike ≈50% endurance volume; run 2–3×/week (`GR-BIKE50`, `P4`).
7. **Key sessions present.** Required key sessions for the phase still exist (possibly shortened, never deleted) unless an injury route explicitly substituted them.
8. **Volume XOR density** for the week (§7).
9. **Phase legality.** No volume progression in Taper; no intensity added before scheduled Build start.

---

## 9. Athlete communication templates `[NARRATOR]`

The narrator fills these *after* the engine decides. Supportive, specific, never alarmist. Each must state the decision, the why (real signals), and the one thing to do.

- **Progress:** "You strung together a clean, consistent block — every key session done and nothing flagged. We're nudging volume up about {pct}% this week, mostly on easy aerobic time. Keep the easy days truly easy and protect your {key_session}."
- **Hold:** "A couple of signals ({signals}) tell me to keep load steady rather than push. I've trimmed {trimmed} and kept your {key_sessions} intact. This week's job: bank sleep and let the body absorb the work — we progress next week once you're green."
- **Deload:** "Fatigue has stacked up ({signals}), so we're taking a planned step back — about {pct}% less volume for {days} days, intensity off, frequency the same. This is a feature, not a setback; you'll come out fresher. Sacred this week: sleep and easy movement only."
- **Bike substitute:** "Your {area} flared on the run, so we're protecting it by shifting that run's load onto an easy bike — same aerobic benefit, far less impact. We'll keep run frequency where it's pain-free and rebuild once it's quiet for two weeks."
- **Gut training:** "Your stomach pushed back on race fueling, so we're training the gut deliberately: I've dialled intake back to {carb} g/h and we'll rehearse on the long ride before ramping. Training load stays put — let's fix tolerance first."

---

## 10. Golden test scenarios `[ENGINE]`

Format — Input → Expected decision → Expected mutations → PlanState delta → Must NOT.

**G1 — All green week → progress.**
Input: all completed, all RPE<8, 0 flags, Base wk5, ≥3 sessions incl. key, 14-day clean.
Decision: `progress`. Mutations: `scale_week_volume(≤1.08)` (intermediate), add easy aerobic. Delta: progression_rate→normal, consecutive_holds=0. Must NOT: exceed +10%; raise volume AND density.

**G2 — Single fatigue flag → hold.**
Input: "poor sleep" once, else green, Base.
Decision: `hold`. Mutations: `scale_non_key_duration(0.90)`, `freeze_progression_rate(1)`. Delta: consecutive_holds=1. Must NOT: deload; cut key session.

**G3 — Three stacked flags → deload.**
Input: RPE≥8 ×3, readiness≤4 ×2, "heavy legs", Build wk3.
Decision: `deload`. Mutations: `scale_week_volume(0.65)`, `strip_intensity_tags()`, preserve frequency. Delta: weeks_since_recovery=0, forced_deload reset. Must NOT: drop session count; remove all easy movement.

**G4 — Easy run RPE 8 + poor sleep → hold (not deload).**
Input: 1 easy run RPE8 + "poor sleep" = 2 flags, no MSK.
Decision: `hold`. Mutations: `scale_non_key_duration(0.85)`, `remove_optional_session()`, freeze 1wk. Must NOT: deload; trigger bike_substitute.

**G5 — Left knee on run → bike_substitute.**
Input: "left knee" on Tue easy run.
Decision: `bike_substitute`. Mutations: `replace_workout(run→bike_endurance)`, `set_run_volume_cap(0.7)`, keep long ride. Delta: run_volume_cap=0.7 (≥2wk). Must NOT: add intensity to sub bike; remove all running.

**G6 — Nausea on long ride → gut_training.**
Input: "nausea" on 4h ride.
Decision: `gut_training`. Mutations: `set_gut_training_mode(true)`, `modify_fueling_notes()` (carb floor down), hold volume. Delta: gut_training_mode=true. Must NOT: deload volume; raise carb target.

**G7 — Two consecutive holds → pull deload forward.**
Input: hold last week + hold this week, Base.
Decision: `deload` (escalated). Mutations: `pull_deload_forward(1)`, `freeze_progression_rate(2)`. Delta: forced_deload_weeks+=next week, progression_rate=frozen. Must NOT: progress; ignore the streak.

**G8 — Missed long run in Build → hold + preserve long ride.**
Input: long run skipped, else green, Build.
Decision: `hold`. Mutations: reschedule/forfeit long run per §5.3, keep long ride intact, no progression. Must NOT: make up long run on adjacent day (`GR-NOHARD2`); cut the long ride; progress.

**G9 — Deload week coinciding with deload signals.**
Input: scheduled deload week + 3 fatigue flags.
Decision: `deload` (single). Mutations: honor deeper cut ≤`GR-DEL50`, extend recovery 1–2 days, `pull_deload_forward`=no-op. Must NOT: double-cut below 50%; add a second deload next week.

**G10 — Taper week with amber signals → hold only.**
Input: 2 flags during Taper.
Decision: `hold`. Mutations: keep taper shape, trim duration not sharpening efforts. Must NOT: progress/increase volume; remove race-pace touches.

**G11 — Returning from illness (4 days off).**
Input: 4 days missed (illness note), then 2 sessions.
Decision: re-entry `deload`/hold override. Mutations: 50% volume, zero intensity, frequency rebuilt, progress disabled 1 wk. Must NOT: schedule full-duration key long session; progress.

**G12 — Insufficient data → hold.**
Input: only 2 completed sessions, no key, plan start.
Decision: `hold (insufficient data)`. Mutations: none/keep stable. Must NOT: progress on sparse data (`P6`).

**G13 — Run niggle single session → niggle handling (not full reroute).**
Input: "shin" on one run, first occurrence.
Decision: `bike_substitute` (scoped). Mutations: replace that one run only; **no** persisted run cap yet. Must NOT: set multi-week run_volume_cap on first occurrence.

**G14 — Gut issues across all sessions → systemic gut_training + hold.**
Input: "stomach" flags on 3 sessions across sports.
Decision: `gut_training`. Mutations: gut_training_mode, lower carb floor aggressively, hold global volume, check illness overlap. Must NOT: deload reflexively; progress.

---

### Open questions summary (recommended defaults implemented above)

1. **Auto-apply low-risk holds?** Default: preview-then-accept (PRD consent), but a hold is the safe fallback so auto-applying it on timeout is acceptable.
2. **How long does post-hold progression freeze persist?** Default: 1 week per hold, 2 weeks after escalated deload.
3. **Auto-shift phase boundaries in v1?** Default: yes, ±1 week max, only within Base/Build, never into Taper.
4. **Equal vs weighted missed-session counting?** Default: weighted (key = 2, optional = 0.5).


---

## Machine-readable ruleset `[ENGINE]`

```playbook
# Machine-readable Adaptation Playbook ruleset.
# Embedded in Adaptation-Playbook.md as playbook fenced blocks.
# The engine parses this file (via the Markdown wrapper) on every evaluation.

version: "1.0"

guardrails:
  max_weekly_increase: 0.10
  max_deload_reduction: 0.50
  default_deload_factor: 0.35
  min_deload_factor: 0.30
  easy_intensity_min_fraction: 0.80
  easy_mandatory_weekly_hours: 15.0
  easy_recommended_weekly_hours: 7.0

windows:
  decision_days: 7
  trend_days: 14
  macro_days: 28

thresholds:
  high_rpe: 8
  low_readiness: 4
  high_rpe_min_sessions: 2
  low_readiness_min_sessions: 2
  deload_flag_count: 3
  hold_flag_count_min: 1
  min_completed_sessions: 3
  min_key_completed_sessions: 1
  partial_week_min_sessions: 5
  consecutive_holds_escalate: 2
  consecutive_deloads_freeze_weeks: 2
  per050_recovery_days_min: 3
  per050_recovery_days_max: 5
  illness_days_off_threshold: 3

flag_weights:
  missed_key_session: 2.0
  missed_optional_session: 0.5
  missed_default_session: 1.0

orthopedic_keywords:
  - knee
  - shin
  - calf
  - achilles
  - foot
  - hip

gi_keywords:
  - gi
  - stomach
  - gut
  - nausea
  - cramp

chronic_orthopedic_min_sessions: 2
chronic_orthopedic_window_days: 14

experience_progress_caps:
  beginner: 0.05
  intermediate: 0.08
  advanced: 0.10

phase_progress_factors:
  prep: 1.0
  base: 1.0
  build: 0.3
  peak: 0.1
  taper: 0.0

experience_hold_trim:
  beginner: 0.20
  intermediate: 0.15
  advanced: 0.10

hold_trim_single_flag: 0.10
hold_trim_multi_flag: 0.20

run_volume_cap:
  beginner: 0.6
  intermediate: 0.7
  advanced: 0.8
  niggle_cap: null
  chronic_weeks_persist: 2
  lift_increment_per_week: 0.1

gut_training:
  carb_floor_default: 60
  carb_ramp_per_week: 5
  systemic_session_threshold: 2

priority_ranks:
  - rank: 1
    name: key_long_ride
    hold_trim_max: 0.10
    deload_trim_max: 0.35
  - rank: 2
    name: key_long_run
    hold_trim_max: 0.15
    deload_trim_max: 0.35
  - rank: 3
    name: race_sim_brick
    hold_trim_max: 0.15
    deload_trim_max: 0.40
  - rank: 4
    name: limiter_quality
    hold_trim_max: 0.20
    deload_strip_intensity: true
  - rank: 5
    name: threshold_vo2
    hold_trim_max: 0.20
    deload_strip_intensity: true
  - rank: 6
    name: technique_swim
    hold_trim_max: 0.20
    deload_trim_max: 0.30
  - rank: 7
    name: strength
    hold_drop_second_session: true
    deload_strip_heavy: true
  - rank: 8
    name: easy_aerobic_filler
    hold_trim_first: true
    deload_trim_max: 0.50
  - rank: 9
    name: optional_second_session
    hold_remove_first: true
    deload_remove: true

decisions:
  progress:
    entry:
      all_completed: true
      all_rpe_below_high: true
      zero_warning_flags: true
      min_completed_sessions: 3
      min_key_completed: 1
      require_14_day_clean: true
      injury_flags_disable: true
    mutations:
      - scale_week_volume
      - add_easy_aerobic
      - advance_progression_rate
    forbidden:
      - volume_and_density_same_week
      - exceed_max_weekly_increase
      - add_fourth_long_run_in_block
      - break_easy_80_20
      - progress_volume_in_taper

  hold:
    entry:
      flag_count_min: 1
      flag_count_max: 2
    mutations:
      - scale_non_key_duration
      - remove_optional_session
      - freeze_progression_rate
    forbidden:
      - cut_key_sessions
      - increase_volume

  deload:
    entry:
      flag_count_min: 3
      consecutive_holds_escalate: 2
    mutations:
      - scale_week_volume
      - strip_intensity_tags
      - insert_recovery_block
      - pull_deload_forward
    forbidden:
      - drop_session_frequency
      - remove_all_easy_movement
      - double_cut_scheduled_deload

  bike_substitute:
    entry:
      sport: run
      orthopedic_keywords_match: true
    mutations:
      - replace_workout
      - set_run_volume_cap
    forbidden:
      - add_intensity_to_substitute_bike
      - remove_all_running

  gut_training:
    entry:
      gi_keywords_match: true
    mutations:
      - set_gut_training_mode
      - modify_fueling_notes
      - hold_global_volume
    forbidden:
      - generic_deload_volume_cut
      - raise_carb_while_symptomatic

macro_rules:
  hold_progression_drop: 1
  clean_week_progression_recover: 1
  consecutive_holds_pull_deload: 1
  base_extension_hold_threshold: 3
  base_extension_deload_threshold: 2
  amber_weeks_cap_peak: 3
  phase_shift_max_weeks: 1

narrator_templates:
  progress: "You strung together a clean, consistent block — every key session done and nothing flagged. We're nudging volume up about {pct}% this week, mostly on easy aerobic time. Keep the easy days truly easy and protect your {key_session}."
  hold: "A couple of signals ({signals}) tell me to keep load steady rather than push. I've trimmed {trimmed} and kept your {key_sessions} intact. This week's job: bank sleep and let the body absorb the work — we progress next week once you're green."
  deload: "Fatigue has stacked up ({signals}), so we're taking a planned step back — about {pct}% less volume for {days} days, intensity off, frequency the same. This is a feature, not a setback; you'll come out fresher. Sacred this week: sleep and easy movement only."
  bike_substitute: "Your {area} flared on the run, so we're protecting it by shifting that run's load onto an easy bike — same aerobic benefit, far less impact. We'll keep run frequency where it's pain-free and rebuild once it's quiet for two weeks."
  gut_training: "Your stomach pushed back on race fueling, so we're training the gut deliberately: I've dialled intake back to {carb} g/h and we'll rehearse on the long ride before ramping. Training load stays put — let's fix tolerance first."

golden_scenarios:
  - id: G1
    name: All green week progress
    phase: base
    week_number: 5
    experience: intermediate
    completions:
      - {completed: true, rpe: 5, readiness_score: 8, is_key: true}
      - {completed: true, rpe: 6, readiness_score: 7}
      - {completed: true, rpe: 5, readiness_score: 8}
    prior_week_clean: true
    expected_decision: progress
    expected_mutations: [scale_week_volume]
    must_not: [exceed_max_weekly_increase, volume_and_density_same_week]

  - id: G2
    name: Single fatigue flag hold
    phase: base
    completions:
      - {completed: true, rpe: 5, fatigue_flags: ["poor sleep"]}
      - {completed: true, rpe: 5}
      - {completed: true, rpe: 6, is_key: true}
    expected_decision: hold
    expected_mutations: [scale_non_key_duration, freeze_progression_rate]
    must_not: [deload, cut_key_session]

  - id: G3
    name: Three stacked flags deload
    phase: build
    week_number: 3
    completions:
      - {completed: true, rpe: 9}
      - {completed: true, rpe: 8}
      - {completed: true, rpe: 9}
      - {completed: true, rpe: 7, readiness_score: 3}
      - {completed: true, rpe: 6, readiness_score: 4}
      - {completed: true, fatigue_flags: ["heavy legs"]}
    expected_decision: deload
    expected_mutations: [scale_week_volume, strip_intensity_tags]
    must_not: [drop_session_count]

  - id: G4
    name: Easy run RPE8 poor sleep hold not deload
    phase: base
    completions:
      - {completed: true, sport: run, rpe: 8}
      - {completed: true, rpe: 5, fatigue_flags: ["poor sleep"]}
      - {completed: true, rpe: 6, is_key: true}
    expected_decision: hold
    expected_mutations: [scale_non_key_duration, remove_optional_session, freeze_progression_rate]
    must_not: [deload, bike_substitute]

  - id: G5
    name: Left knee bike substitute
    phase: base
    completions:
      - {completed: true, sport: run, fatigue_flags: ["left knee"]}
      - {completed: true, rpe: 5, is_key: true}
      - {completed: true, rpe: 6}
    expected_decision: bike_substitute
    expected_mutations: [replace_workout, set_run_volume_cap]
    must_not: [add_intensity_to_substitute_bike, remove_all_running]

  - id: G6
    name: Nausea gut training
    phase: build
    completions:
      - {completed: true, sport: bike, fatigue_flags: ["nausea"], is_key: true}
      - {completed: true, rpe: 5}
    expected_decision: gut_training
    expected_mutations: [set_gut_training_mode, modify_fueling_notes]
    must_not: [deload_volume, raise_carb_target]

  - id: G7
    name: Two consecutive holds escalate deload
    phase: base
    plan_state:
      consecutive_holds: 1
    completions:
      - {completed: true, rpe: 5, fatigue_flags: ["poor sleep"]}
      - {completed: true, rpe: 6}
      - {completed: true, rpe: 5, is_key: true}
    expected_decision: deload
    expected_mutations: [pull_deload_forward, freeze_progression_rate]
    must_not: [progress]

  - id: G8
    name: Missed long run hold preserve long ride
    phase: build
    completions:
      - {completed: false, sport: run, is_key: true}
      - {completed: true, sport: bike, rpe: 5, is_key: true}
      - {completed: true, rpe: 6}
    expected_decision: hold
    must_not: [progress, cut_long_ride]

  - id: G9
    name: Deload week coinciding with signals
    phase: build
    is_deload_week: true
    completions:
      - {completed: true, rpe: 9}
      - {completed: true, rpe: 8}
      - {completed: true, rpe: 9}
      - {completed: true, fatigue_flags: ["heavy legs"]}
    expected_decision: deload
    must_not: [double_cut_below_50_percent]

  - id: G10
    name: Taper amber hold only
    phase: taper
    completions:
      - {completed: true, rpe: 5, fatigue_flags: ["poor sleep"]}
      - {completed: true, rpe: 6, fatigue_flags: ["heavy legs"]}
      - {completed: true, rpe: 5, is_key: true}
    expected_decision: hold
    must_not: [progress, increase_volume]

  - id: G11
    name: Returning from illness
    phase: base
    illness_days_off: 4
    completions:
      - {completed: true, rpe: 4}
      - {completed: true, rpe: 5}
    expected_decision: deload
    must_not: [progress, full_duration_key_long]

  - id: G12
    name: Insufficient data hold
    phase: base
    completions:
      - {completed: true, rpe: 5}
      - {completed: true, rpe: 6}
    expected_decision: hold
    insufficient_data: true
    must_not: [progress]

  - id: G13
    name: Run niggle single session scoped
    phase: base
    completions:
      - {completed: true, sport: run, fatigue_flags: ["shin"]}
      - {completed: true, rpe: 5, is_key: true}
      - {completed: true, rpe: 6}
    expected_decision: bike_substitute
    expected_mutations: [replace_workout]
    must_not: [set_run_volume_cap]

  - id: G14
    name: Gut issues systemic
    phase: build
    completions:
      - {completed: true, sport: bike, fatigue_flags: ["stomach"]}
      - {completed: true, sport: run, fatigue_flags: ["stomach"]}
      - {completed: true, sport: swim, fatigue_flags: ["stomach"]}
    expected_decision: gut_training
    must_not: [deload, progress]

```
