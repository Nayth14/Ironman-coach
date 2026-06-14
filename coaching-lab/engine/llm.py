"""Thin OpenAI client wrapper.

Centralizes model selection and keeps the rest of the engine provider-agnostic
in shape (so the TypeScript port maps cleanly to packages/llm).
"""

from __future__ import annotations

import os
from typing import Iterator

from openai import BadRequestError, OpenAI

_client: OpenAI | None = None


def _is_unsupported_temperature_error(err: BadRequestError) -> bool:
    """Some models (e.g. GPT-5 / o-series reasoning models) only allow the
    default temperature. Detect that specific 400 so we can retry without it."""
    return getattr(err, "param", None) == "temperature" or "temperature" in str(err)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def chat_model() -> str:
    return os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o")


def extract_model() -> str:
    return os.environ.get("OPENAI_EXTRACT_MODEL", "gpt-4o")


def summary_model() -> str:
    return os.environ.get("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")


def workout_model() -> str:
    return os.environ.get("OPENAI_WORKOUT_MODEL", "gpt-4o-mini")


Message = dict[str, str]


def stream_chat(system: str, messages: list[Message], model: str | None = None) -> Iterator[str]:
    """Stream a chat completion, yielding text deltas."""
    client = _get_client()
    full_messages = [{"role": "system", "content": system}, *messages]
    kwargs = dict(model=model or chat_model(), messages=full_messages, stream=True)
    try:
        stream = client.chat.completions.create(temperature=0.6, **kwargs)
    except BadRequestError as err:
        if not _is_unsupported_temperature_error(err):
            raise
        stream = client.chat.completions.create(**kwargs)
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def complete_chat(system: str, messages: list[Message], model: str | None = None) -> str:
    """Non-streaming chat completion."""
    client = _get_client()
    full_messages = [{"role": "system", "content": system}, *messages]
    kwargs = dict(model=model or chat_model(), messages=full_messages)
    try:
        resp = client.chat.completions.create(temperature=0.6, **kwargs)
    except BadRequestError as err:
        if not _is_unsupported_temperature_error(err):
            raise
        resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def complete_json(system: str, user_content: str, schema: dict, model: str | None = None) -> str:
    """Structured JSON completion using a JSON schema response format."""
    client = _get_client()
    kwargs = dict(
        model=model or extract_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "athlete_profile",
                "schema": schema,
                "strict": False,
            },
        },
    )
    try:
        resp = client.chat.completions.create(temperature=0, **kwargs)
    except BadRequestError as err:
        if not _is_unsupported_temperature_error(err):
            raise
        resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or "{}"
