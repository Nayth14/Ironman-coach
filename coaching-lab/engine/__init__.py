"""Coaching engine for Nayth's Ironman Coach.

This package is the source of truth for all coaching logic. The Streamlit app
(`app.py`) is only a thin UI over these modules. When we move to the main app,
this package ports to `packages/core` in TypeScript with the same schemas,
rules, and test cases.

Nothing in this package should import Streamlit. Import submodules directly,
e.g. `from engine import plan, readiness, strength`.
"""
