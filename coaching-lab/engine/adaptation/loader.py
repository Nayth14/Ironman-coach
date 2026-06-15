"""Load and cache the Adaptation Playbook on every evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.adaptation.parser import parse_markdown, parse_playbook_file, parse_yaml_file, playbook_checksum
from engine.adaptation.spec import PlaybookSpec

_DEFAULT_PLAYBOOK_DIR = Path(__file__).resolve().parents[2] / "playbook"
_MARKDOWN_PATH = _DEFAULT_PLAYBOOK_DIR / "Adaptation-Playbook.md"
_YAML_PATH = _DEFAULT_PLAYBOOK_DIR / "playbook-data.yaml"


@dataclass(frozen=True, slots=True)
class LoadedPlaybook:
    spec: PlaybookSpec
    version: str
    checksum: str
    source_path: str


_cache: dict[str, LoadedPlaybook] = {}


def _resolve_paths(playbook_path: Path | None) -> tuple[Path, Path]:
    if playbook_path is not None:
        if playbook_path.suffix == ".yaml":
            return playbook_path.parent / "Adaptation-Playbook.md", playbook_path
        return playbook_path, playbook_path.parent / "playbook-data.yaml"
    return _MARKDOWN_PATH, _YAML_PATH


def load_playbook(playbook_path: Path | None = None, *, force_reload: bool = False) -> LoadedPlaybook:
    """Load playbook; re-parse when checksum changes."""
    if playbook_path is not None and playbook_path.suffix in (".yaml", ".yml"):
        content = playbook_path.read_text(encoding="utf-8")
        checksum = playbook_checksum(content)
        if not force_reload and checksum in _cache:
            return _cache[checksum]
        spec = parse_yaml_file(playbook_path)
        loaded = LoadedPlaybook(
            spec=spec,
            version=spec.version,
            checksum=checksum,
            source_path=str(playbook_path),
        )
        _cache[checksum] = loaded
        return loaded

    md_path, yaml_path = _resolve_paths(playbook_path)

    if md_path.exists() and "```playbook" in md_path.read_text(encoding="utf-8"):
        content = md_path.read_text(encoding="utf-8")
        checksum = playbook_checksum(content)
        if not force_reload and checksum in _cache:
            return _cache[checksum]
        spec = parse_markdown(content)
        loaded = LoadedPlaybook(
            spec=spec,
            version=spec.version,
            checksum=checksum,
            source_path=str(md_path),
        )
        _cache[checksum] = loaded
        return loaded

    if yaml_path.exists():
        content = yaml_path.read_text(encoding="utf-8")
        checksum = playbook_checksum(content)
        if not force_reload and checksum in _cache:
            return _cache[checksum]
        spec = parse_yaml_file(yaml_path)
        loaded = LoadedPlaybook(
            spec=spec,
            version=spec.version,
            checksum=checksum,
            source_path=str(yaml_path),
        )
        _cache[checksum] = loaded
        return loaded

    raise FileNotFoundError(f"Adaptation Playbook not found at {md_path} or {yaml_path}")


def clear_cache() -> None:
    _cache.clear()
