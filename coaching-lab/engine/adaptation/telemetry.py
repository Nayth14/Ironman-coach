"""Adaptation telemetry events."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("adaptation.telemetry")


class TelemetryEvent(str, Enum):
    TRIGGERED = "adaptation_triggered"
    ACCEPTED = "adaptation_accepted"
    DISMISSED = "adaptation_dismissed"
    APPLY_SUCCESS = "adaptation_apply_success"
    APPLY_FAILURE = "adaptation_apply_failure"
    VALIDATION_FAILURE = "adaptation_validation_failure"


def emit(
    event: TelemetryEvent,
    *,
    athlete_id: str | None = None,
    event_id: str | None = None,
    decision: str | None = None,
    playbook_version: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = {
        "event": event.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "athlete_id": athlete_id,
        "adaptation_event_id": event_id,
        "decision": decision,
        "playbook_version": playbook_version,
        **(extra or {}),
    }
    logger.info("adaptation_telemetry %s", json.dumps(payload, default=str))


# Feature flag: preview-then-accept by default; hold may auto-apply when enabled.
AUTO_APPLY_HOLD = False
