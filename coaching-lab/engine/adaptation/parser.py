"""Parse Adaptation Playbook Markdown and YAML into PlaybookSpec."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from engine.adaptation.spec import PlaybookSpec

PLAYBOOK_FENCE = re.compile(r"```playbook\s*\n(.*?)```", re.DOTALL)


def extract_playbook_blocks(markdown: str) -> list[dict]:
    """Extract and merge all ```playbook fenced YAML blocks."""
    blocks: list[dict] = []
    for match in PLAYBOOK_FENCE.finditer(markdown):
        data = yaml.safe_load(match.group(1))
        if data:
            blocks.append(data)
    return blocks


def _merge_blocks(blocks: list[dict]) -> dict:
    if not blocks:
        return {}
    merged = dict(blocks[0])
    for block in blocks[1:]:
        for key, value in block.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = {**merged[key], **value}
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = merged[key] + value
            else:
                merged[key] = value
    return merged


def parse_markdown(markdown: str) -> PlaybookSpec:
    blocks = extract_playbook_blocks(markdown)
    if not blocks:
        raise ValueError("No ```playbook fenced blocks found in Adaptation Playbook")
    merged = _merge_blocks(blocks)
    return PlaybookSpec.model_validate(merged)


def parse_yaml_file(path: Path) -> PlaybookSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PlaybookSpec.model_validate(data)


def parse_playbook_file(path: Path) -> PlaybookSpec:
    """Parse playbook from Markdown (preferred) or standalone YAML."""
    text = path.read_text(encoding="utf-8")
    if "```playbook" in text:
        return parse_markdown(text)
    return parse_yaml_file(path)


def playbook_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
