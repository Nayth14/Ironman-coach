# PRD: Fully Adaptable Planning (Adaptions v1)

- **Version:** 1.0
- **Date:** 2026-06-15
- **Status:** Draft
- **Product Area:** Coaching Engine + Dashboard
- **Related ADR:** ADR-001 Fully Adaptable Planning Engine
- **Authoritative Ruleset:** [`coaching-lab/playbook/Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md) — the canonical coaching ruleset behind every adaptation. This PRD defines product behavior and surfaces; the Playbook defines the decisions and mutations the engine executes.

## 1. Executive Summary

We will evolve adaptation from a recommendation-only experience into a fully executable, deterministic coaching loop that updates both:
1. immediate upcoming workouts, and
2. long-term plan trajectory.

Goal: the app should behave like a high-quality coach safely, transparently, and consistently when athlete feedback signals fatigue, readiness changes, orthopedic risk, or fueling issues.

## 2. Problem Statement

Current behavior can classify adaptation state but does not always mutate the plan itself. This weakens trust and limits coaching impact.

Users need:
- concrete and visible plan changes after adaptation acceptance
- progression logic that reflects recent athlete response
- safe and conservative auto-adjustments aligned with Ironman coaching principles

## 3. Goals

### Primary Goals

- Make adaptation **actionable** (real plan mutations, not just text)
- Support both **micro** (next week) and **macro** (future trajectory) adaptation
- Preserve deterministic safety and explainability
- Keep user control via accept/dismiss

### Success Criteria

- 95%+ accepted adaptation events produce at least one persisted workout or plan-state change
- 100% mutated plans pass hard-rule validation
- Adaptation acceptance rate increases by >=20% vs baseline
- Time from acceptance to visible plan update < 1s p95

## 4. Non-Goals (v1)

- LLM deciding training load
- Fully autonomous phase redesign without deterministic constraints
- Device-native auto sync changes (Garmin/TP) in this milestone
- Replacing coach chat with adaptation engine

## 5. Users & Personas

- **Primary:** Self-coached age-group Ironman athlete (8-14 h/week), needs practical automatic adjustments
- **Secondary:** Returning athlete with injury history, requires conservative progression and run protection

## 6. Product Principles

- Durability first
- Conservative progression over aggressive gains
- Rule-based load control
- Explain what changed and why
- User consent before applying mutations
- Recovery is a feature, not a failure
- **The Adaptation Playbook is the single source of truth.** All adaptation logic derives from [`Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md); the engine reads it rather than relying on hardcoded rules, and it is amended by coaches over time as a versioned ruleset.

## 7. User Stories

1. As an athlete, I want accepted adaptations to immediately modify my upcoming sessions.
2. As an athlete, I want to see exactly what changed (before/after) and why.
3. As an athlete, I want fatigue and poor sleep to slow progression safely.
4. As an athlete with run niggles, I want run load shifted safely to bike when needed.
5. As a product team, we want adaptation changes to be auditable and testable.

## 8. Functional Requirements

### 8.0 Playbook-Driven Decisioning (source of truth)

- The engine MUST derive every adaptation decision and mutation from [`Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md). No adaptation rule (threshold, flag weight, priority order, phase modifier, progression formula) may live only in code where it contradicts the Playbook.
- The Playbook is **versioned, amendable data, not code.** Coaches/coaching engineers will change thresholds, add scenarios, and refine modifiers without shipping a new engine build.
- On **every** adaptation evaluation the engine MUST load and parse the current Playbook (a cache keyed on Playbook version/checksum is permitted) so that an amended Playbook takes effect without a code deploy.
- Every decision MUST record the **Playbook version** it was evaluated against (stored on the adaptation event) for auditability and reproducibility.
- Only `[ENGINE]`-tagged rules are executable; `[NARRATOR]` content feeds the LLM explanation only; `[OPEN QUESTION]` defaults are active until amended.
- Hard guardrails (`GR-*`) are additionally enforced as code-level invariants so the engine can never exceed a safety limit even if the Playbook is amended incorrectly; the Playbook may be more conservative than the floor, never less.
- The Playbook §10 golden scenarios serve as the acceptance/conformance suite and MUST run in CI against the live Playbook.

### 8.1 Signal Aggregation

- Aggregate signals across 7-day, 14-day, and 28-day windows
- Track:
  - completion consistency
  - high-RPE frequency
  - low-readiness frequency
  - fatigue flags
  - missed key sessions
- Require minimum data threshold before progress decisions

### 8.2 Decision Engine

Supported decisions:
- `progress`
- `hold`
- `deload`
- `bike_substitute`
- `gut_training`

Decision rules remain deterministic and capped by hard guardrails.

### 8.3 Plan Mutation Engine

On accept, apply machine-readable mutation ops to:
- materialized weeks (immediate plan)
- PlanState (future generation trajectory)

Required mutation operations:
- scale weekly volume
- trim optional non-key volume
- preserve key sessions by priority
- replace selected run with bike endurance where indicated
- force short recovery block where indicated
- update fueling session prescriptions
- adjust progression rate (freeze/slow/recover)

### 8.4 PlanState

Persist per active plan:
- volume multiplier
- progression rate
- forced deload flags
- run volume cap
- gut-training mode
- consecutive holds counter
- recent decision history

### 8.5 Validation & Safety

Every mutation must pass:
- scheduling constraints
- intensity distribution constraints
- phase/taper constraints
- weekly increase/decrease caps
- run safety constraints

Failure behavior:
- reject unsafe mutation
- fallback to safest valid alternative (`hold` profile)
- log failure reason

### 8.6 API Behavior

- `POST /adaptations/evaluate`: returns decision + preview diff + mutation payload
- `POST /adaptations/{id}/accept`: applies mutations, persists plan and state, returns applied diff
- `POST /adaptations/{id}/dismiss`: marks event dismissed; no mutations

### 8.7 UI/UX Requirements

- Adaptation panel shows:
  - decision
  - rationale
  - signals
  - before/after diff (hours, sessions changed, substitutions)
- On accept:
  - updated week cards and plan timeline refresh immediately
- Show `applied` badge on adapted workouts

## 9. Detailed Behavior by Decision Type

> The summaries below are a product-level overview. The **authoritative** entry criteria, ordered/forbidden mutations, phase + experience + injury modifiers, and worked examples for each decision live in [`Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md) §4. If this section and the Playbook ever disagree, the Playbook wins and this section is updated to match.

### Progress

- Preconditions: high compliance, no warning flags
- Mutations:
  - +5-10% load cap
  - or modest density increase (not both simultaneously)
- Never violate 80/20 or scheduling constraints

### Hold

- Preconditions: mild warning profile
- Mutations:
  - keep weekly load stable
  - trim optional volume by 10-20%
  - preserve key sessions
  - freeze progression for short horizon

### Deload

- Preconditions: stacked warning profile
- Mutations:
  - reduce 30-50% volume for 3-7 days or week-level equivalent
  - remove intensity, preserve easy frequency
  - protect durability and recovery behaviors

### Bike Substitute

- Preconditions: run orthopedic stress signals
- Mutations:
  - reduce run intensity/volume
  - replace selected run with low-impact bike endurance
  - temporary run cap via PlanState

### Gut Training

- Preconditions: GI/fueling intolerance signals
- Mutations:
  - progressive fueling prescriptions
  - simplify fueling strategy in long sessions
  - avoid unnecessary global load increase until stabilized

## 10. Data Model Requirements

### New/Extended Entities

- `PlanState` (attached to training plan)
- `PlanMutation` (stored in adaptation event payload)
- `AdaptationEvent` extended with:
  - proposed_mutations
  - applied_mutations
  - pre/post checksums
  - application_status
  - application_error (nullable)
  - `playbook_version` (the Playbook version/checksum the decision was evaluated against)

## 11. Telemetry & Analytics

Track:
- adaptation triggered/accepted/dismissed
- mutation apply success/failure
- rule validation failures by type
- subsequent athlete signals 7/14/28 days after adaptation
- retention and engagement impact

## 12. Non-Functional Requirements

- Determinism: same inputs -> same decision/mutation output
- Performance: apply + refresh < 1s p95 for active week
- Reliability: no partial writes (transactional apply path)
- Auditability: full immutable event and diff history
- Explainability: rationale references actual mutations

## 13. Rollout Plan

### Phase 1 (Core)

- PlanState schema + migration
- Hold/Progress/Deload mutator
- Accept applies real changes

### Phase 2 (Specialized)

- Bike Substitute and Gut Training mutators
- Enhanced preview diffs

### Phase 3 (Trajectory)

- Multi-week trajectory adaptation via PlanState
- Rolling extension for future weeks

### Phase 4 (Optimization)

- Calibration using telemetry and coach review
- Add confidence scoring and scenario tuning

## 14. Acceptance Criteria

1. Accepted adaptation updates at least one of:
   - workout details
   - week target load
   - PlanState trajectory
2. Updated plan remains rule-valid post-apply
3. UI shows clear before/after diff
4. Dismiss leaves plan unchanged
5. Adapted state persists across reloads/devices
6. Regression test suite passes for all decision paths

## 15. Risks & Open Questions

### Risks

- Adaptation over-correcting on sparse data
- Edge-case conflicts during peak/taper
- User confusion if changes are too opaque

### Open Questions

- Should we auto-apply low-risk Hold adjustments by default?
- How long should progression freeze persist after consecutive holds?
- Should repeated holds shift phase boundaries automatically in v1 or v2?

## 16. Appendix: Example v1 Test Scenarios

> The canonical, full set of conformance scenarios lives in [`Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md) §10 (Golden test scenarios) and is the suite engineering must implement. The list below is an illustrative subset.

- Single fatigue flag (poor sleep) -> Hold + optional trim
- 3 warning flags -> Deload + intensity removal
- Run pain keyword -> Bike substitute
- GI keyword on long ride -> Gut training adjustments
- Clean 14-day compliance -> Progress with <=10% cap
- Taper week warning -> Hold/Deload only, no progression
