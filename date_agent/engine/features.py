# Normalize source-specific fields, then validate using the Candidate model.

import logging

from candidate import Candidate
from tags import IndoorOutdoor

log = logging.getLogger(__name__)


def extract_features(raw: dict) -> dict:
    """Return a validated dictionary ready for scoring.

    Legacy seeds use name, indoor, duration_hours, and energy_level. Keep that
    translation here; Candidate owns field validation and tag filtering.
    """
    normalized = dict(raw)
    name = raw.get("content") or raw.get("name") or raw.get("description", "unknown")
    normalized["content"] = name

    if raw.get("indoor_outdoor") is None and "indoor" in raw:
        normalized["indoor_outdoor"] = IndoorOutdoor.INDOOR if raw["indoor"] else IndoorOutdoor.OUTDOOR

    if raw.get("duration_minutes") is None and raw.get("duration_hours") is not None:
        try:
            normalized["duration_minutes"] = int(float(raw["duration_hours"]) * 60)
        except (TypeError, ValueError, OverflowError):
            log.warning("candidate '%s': invalid duration_hours=%r — setting duration to None", name, raw["duration_hours"])
            normalized["duration_minutes"] = None

    if raw.get("effort_level") is None:
        normalized["effort_level"] = raw.get("energy_level")

    candidate = Candidate.model_validate(normalized).model_dump(mode="json")
    log.debug(
        "features | '%s' → tags=%s vibe=%s price=%s neighborhood=%s io=%s",
        name, candidate["tags"], candidate["vibe"],
        candidate["price_tier"], candidate["neighborhood"], candidate["indoor_outdoor"],
    )
    return candidate
