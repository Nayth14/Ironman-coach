# ADR-001: Fully Adaptable Planning Engine

- **Status:** Proposed
- **Date:** 2026-06-15
- **Owner:** Coaching Engine Team
- **Decision Drivers:** Athlete safety, deterministic behavior, explainability, product trust, future extensibility
- **Authoritative Ruleset:** [`coaching-lab/playbook/Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md) — the single source of truth for every adaptation decision and mutation. This ADR defines the *architecture*; the Playbook defines the *rules*.

## Context

The current adaptation flow classifies athlete feedback into decisions (`progress`, `hold`, `deload`, `bike_substitute`, `gut_training`) and stores adaptation events, but it does not consistently mutate upcoming weeks or long-term plan trajectory.

This creates a gap between:
1. **What the app says** ("your coach adjusted this week"), and
2. **What the plan actually does** (often unchanged workout structure).

For Ironman coaching, good adaptation must work at two levels:
- **Micro-level:** upcoming week/session edits
- **Macro-level:** progression trajectory across future weeks and phases

The system must remain deterministic and auditable; LLM output is explanatory only.

## Decision

We will implement a deterministic **Adaptation Playbook + Plan Mutator** architecture with persistent **PlanState**, enabling both immediate workout changes and future-week trajectory changes.

### 0) The Adaptation Playbook is the authoritative ruleset

[`Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md) is the single, canonical source for **all** adaptation behavior: signal aggregation windows, the decision ladder, warning-flag definitions, the session priority hierarchy, per-decision mutation playbooks, progression math, validation checks, and golden test scenarios.

- The engine must **not** hardcode adaptation rules that duplicate or diverge from the Playbook. Where today's `engine/adaptation.py` encodes rules inline, those rules are considered a cached implementation of the Playbook and must be reconciled to it.
- The Playbook is **expected to change over time.** Coaches will amend thresholds, flag weights, phase modifiers, and add scenarios. The architecture must treat the ruleset as **versioned data, not code.**
- **The engine parses the Playbook on every adaptation evaluation** (subject to caching, below) so that an amended Playbook changes engine behavior without a code deploy. Each `AdaptationResult` and `AdaptationEvent` must record the **Playbook version** it was evaluated against, for auditability and reproducibility.
- Only `[ENGINE]`-tagged rules are executable. `[NARRATOR]` content is passed to the LLM for explanation only and never influences the decision or load. `[OPEN QUESTION]` defaults are treated as the active rule until the Playbook is amended.

This makes the Playbook a contract: engineers implement a **deterministic parser + interpreter** for it, not a fixed set of rules.

### 1) Deterministic adaptation pipeline

Adopt and enforce this server-side pipeline:

`load + parse Playbook (versioned) -> completion signals -> signal aggregator -> adaptation rules (from Playbook) -> plan mutator -> validation (against Playbook) -> persistence (incl. Playbook version) -> LLM narration (from [NARRATOR] templates)`

### 2) Introduce persistent PlanState

Each active plan will include mutable planning state (stored with training plan metadata), including:

- `volume_multiplier` (global load scalar)
- `progression_rate` (ramp aggressiveness)
- `forced_deload_weeks` (explicit recovery inserts)
- `run_volume_cap` (injury-protective cap)
- `gut_training_mode` (fueling constraint mode)
- `consecutive_holds`
- `recent_decision_history`

Plan generation and week extension must consume PlanState.

### 3) Introduce machine-readable PlanMutations

Adaptation decisions must emit both:
- human-readable `changes[]`
- machine-readable `mutations[]` for execution

Mutation operations include:
- `scale_week_volume`
- `trim_optional_sessions`
- `replace_workout`
- `strip_intensity`
- `force_deload_block`
- `update_fueling_prescriptions`
- `freeze_or_reduce_progression_rate`
- `set_run_volume_cap`

### 4) Split adaptation into two layers

- **Micro adaptations:** apply to materialized weeks (e.g., current + next 1-3 weeks)
- **Macro adaptations:** update PlanState for unmaterialized future weeks

### 5) Keep deterministic safety guardrails

All mutations must satisfy hard coaching constraints:
- Max weekly increase <= 10%
- Max deload reduction <= 50%
- 80/20 intensity constraints
- No unsafe scheduling conflicts
- Conservative run progression
- Deload keeps frequency while reducing duration
- Existing ruleset validation must pass after mutation

### 6) Add explicit apply/preview behavior

- `evaluate`: compute decision + proposed mutations (preview/dry run)
- `accept`: apply mutations, persist changes, update PlanState
- `dismiss`: record rejection, no mutation

## Architecture Changes

### Playbook loading & interpretation

- Add a **Playbook loader/parser** that reads [`Adaptation-Playbook.md`](../../coaching-lab/playbook/Adaptation-Playbook.md) (or a structured artifact derived from it) and exposes its `[ENGINE]` rules — windows, thresholds, flag weights, priority hierarchy, mutation playbooks, progression math, and validation checks — to the decision engine.
- The engine **re-parses (or reads a cached parse of) the Playbook on every evaluation.** Caching is allowed for performance, but the cache key must include the Playbook **version/checksum** so any amendment invalidates the cache and changes behavior without a code deploy.
- Each evaluation stamps the resolved **Playbook version** onto the `AdaptationResult` and persisted `AdaptationEvent`, so any past decision can be reproduced against the exact ruleset that produced it.
- The parser is itself deterministic and unit-tested; the Playbook's §10 golden scenarios are the conformance suite for the loader + engine together.
- **Safety floor:** the hard guardrails (`GR-*` in the Playbook, e.g. max +10%/week, max 50% deload, 80/20) are also enforced as code-level invariants in the validator, so a malformed or maliciously-amended Playbook can never push the plan past a guardrail. The Playbook may be *more* conservative than the floor, never less.

### Domain

- Add `PlanState` model
- Add `PlanMutation` model
- Extend `AdaptationResult` to include `mutations`, `plan_state_delta`, and `playbook_version`

### Persistence

- Store PlanState on active training plan
- Store mutation payload and application result per adaptation event
- Store pre/post plan checksum for auditability

### API

- Keep evaluate endpoint, return deterministic preview diff
- Add/extend apply endpoint to execute accepted adaptation
- Return changed weeks/workouts and state deltas for UI rendering

### Validation

- Re-run week and plan validators after mutation
- Reject and fail-safe to `hold` when mutation would violate hard constraints

## Consequences

### Positive

- Real adaptation behavior matches user-visible coaching claims
- Full audit trail for every plan mutation
- Safer progression with deterministic constraints
- Better product trust and measurable coaching quality

### Tradeoffs

- More domain complexity (state + mutation ops)
- Need broader test matrix (decision x phase x athlete profile)
- Requires migration and backward compatibility for existing plans

### Risks & Mitigations

- **Risk:** Over-aggressive mutations  
  **Mitigation:** conservative defaults + hard caps + validator gate
- **Risk:** Rule conflicts in edge phases (peak/taper)  
  **Mitigation:** phase-specific mutation constraints
- **Risk:** Explainability mismatch  
  **Mitigation:** LLM consumes exact mutation payload, not inferred narrative
- **Risk:** A Playbook amendment introduces an unsafe or malformed rule  
  **Mitigation:** code-level guardrail floor (`GR-*`) always validates the final mutation; Playbook can only be *more* conservative; parser rejects malformed rules and fails safe to `hold`
- **Risk:** Engine behavior silently drifts from the Playbook (stale hardcoded rules)  
  **Mitigation:** Playbook is the source of truth, parsed each evaluation; §10 golden scenarios run in CI against the live Playbook; decisions stamp `playbook_version`

## Rollout Plan

1. Implement the Playbook loader/parser + version stamping; wire §10 golden scenarios as the conformance suite
2. Implement PlanState and mutation schema
3. Implement Hold/Progress/Deload mutator (core path)
4. Add Bike Substitute and Gut Training specialized mutators
5. Enable preview diff in UI
6. Enable accept/apply persistence path
7. Add macro extension logic for future weeks
8. Ship with feature flag and telemetry review

## Success Metrics

- >=95% accepted adaptations produce concrete plan deltas
- 0 hard-rule violations post-mutation in production
- Increased adaptation acceptance rate
- Reduction in repeated warning-flag cascades over 2-4 weeks
- Higher perceived trust in coaching adjustments (qualitative UX measure)
