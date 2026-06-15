# Coaching Lab — Nayth's Ironman Coach

A local sandbox to **nail the coaching logic** before building the main app. It's
a Streamlit chat app over a standalone `engine/` package. The engine is the
source of truth and ports to `packages/core` (TypeScript) in the main app later.

## Principle

> The LLM (OpenAI) handles conversation and explanation.
> **Deterministic Python owns all training-load decisions.**

`app.py` is only UI. Every coaching decision lives in `engine/`.

## Structure

```
coaching-lab/
├── app.py                  # Streamlit chat UI (no coaching logic here)
├── smoke_test.py           # Offline engine check (no OpenAI needed)
├── engine/
│   ├── models.py           # Canonical schemas (mirror docs/ADR.md)
│   ├── llm.py              # OpenAI wrapper (models, streaming, JSON)
│   ├── extract.py         # Chat -> structured AthleteProfile
│   ├── readiness.py       # green/amber/red timeline + safety verdict
│   ├── strength.py        # Strength prescription from background + injuries
│   ├── periodization.py   # Prep -> Base -> Build -> Peak -> Taper
│   ├── scheduler.py       # Weekly calendar of workouts
│   ├── plan.py            # Orchestrates a full TrainingPlan
│   ├── adaptation/        # Playbook-driven progress / hold / deload engine
│   │   ├── loader.py      # Loads + caches Adaptation-Playbook.md each eval
│   │   ├── parser.py      # Parses ```playbook fenced YAML blocks
│   │   ├── signals.py     # 7/14/28-day signal aggregation
│   │   ├── decide.py      # Decision ladder from PlaybookSpec
│   │   ├── mutate.py      # Plan mutation operations
│   │   ├── apply.py       # Apply mutations to materialized weeks
│   │   ├── trajectory.py  # PlanState macro rules
│   │   └── guardrails.py  # GR-* hard floor validation
│   ├── fixtures.py        # Load saved personas
│   └── prompts/           # System prompts (port to packages/llm)
├── playbook/              # Authoritative adaptation ruleset (parsed by engine)
│   ├── Adaptation-Playbook.md
│   └── playbook-data.yaml
└── fixtures/              # Saved athlete personas for regression
```

## Setup

```bash
cd "coaching-lab"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then add your OPENAI_API_KEY
```

## Run

```bash
# Full chat lab (needs OPENAI_API_KEY)
streamlit run app.py

# Offline engine check (no API key needed)
python smoke_test.py
```

## Workflow

1. Use the chat to talk to the onboarding coach, or load a persona from the sidebar.
2. Inspect the extracted profile, readiness verdict, strength plan, phases, and weeks.
3. Use **Simulate a week of feedback** to test the adaptation engine.
4. Tweak rules in `engine/`, re-run `smoke_test.py` against all personas, compare.
5. Once happy, port the engine + prompts into the main app.

## Adding a persona

Drop a YAML file in `fixtures/` matching the existing shape. It appears in the
sidebar and in `smoke_test.py` automatically.
