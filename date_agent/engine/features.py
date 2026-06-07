# engine/features.py
# Stage 2 of the pipeline: normalize raw candidate dicts into validated Candidate TypedDicts.
#
# Every candidate from sources/ (seeds, Eventbrite, DDG, etc.) passes through
# extract_features() before it reaches the scoring engine. This is the single place
# that enforces the tag vocabulary defined in tags.py.

import logging
from candidate import Candidate
from tags import (
    ALL_KNOWN_TAGS,
    ActivityTag,
    CuisineTag,
    DataSource,
    IndoorOutdoor,
    NeighborhoodTag,
    PriceTier,
    VibeTag,
)

log = logging.getLogger(__name__)

# Numeric price tier values used by sources/seeds.py → string PriceTier mapping
_PRICE_TIER_INT_MAP: dict[int, str] = {
    1: PriceTier.BUDGET.value,
    2: PriceTier.MID.value,
    3: PriceTier.UPSCALE.value,
}


def validate_tags(raw_tags: list[str], candidate_name: str = "unknown") -> list[str]:
    """Normalize and validate a list of raw tag strings against the known vocabulary.

    Unknown tags are dropped with a WARNING so the developer knows to add them to tags.py
    if they should be permanent. Never raises — callers always get a (possibly empty) list.
    """
    clean: list[str] = []
    for t in raw_tags:
        normalized = t.strip().lower()
        if normalized in ALL_KNOWN_TAGS:
            clean.append(normalized)
        else:
            log.warning(
                "candidate '%s': unknown tag '%s' dropped — add to tags.py if permanent",
                candidate_name, t,
            )
    return clean


def _validate_enum_field(value, enum_class, field_name: str, candidate_name: str) -> str | None:
    """Try to coerce value to a valid Enum member; return the string value or None on failure."""
    if value is None:
        return None
    try:
        return enum_class(value).value
    except ValueError:
        log.warning(
            "candidate '%s': unknown %s='%s' — setting to None",
            candidate_name, field_name, value,
        )
        return None


def extract_features(raw: dict) -> Candidate:
    """Normalize a raw candidate dict (from any source) into a validated Candidate.

    Handles format differences between sources:
    - seeds.py uses `name` instead of `content`
    - seeds.py uses `indoor: bool` instead of `indoor_outdoor: str`
    - seeds.py uses `price_tier: int` (1/2/3) instead of "budget"/"mid"/"upscale"
    - seeds.py uses `duration_hours` instead of `duration_minutes`
    """
    name = raw.get("content") or raw.get("name") or raw.get("description", "unknown")

    # ------------------------------------------------------------------
    # Normalize legacy seeds.py fields
    # ------------------------------------------------------------------
    raw_io = raw.get("indoor_outdoor")
    if raw_io is None and "indoor" in raw:
        raw_io = IndoorOutdoor.INDOOR.value if raw["indoor"] else IndoorOutdoor.OUTDOOR.value

    raw_price = raw.get("price_tier")
    if isinstance(raw_price, int):
        raw_price = _PRICE_TIER_INT_MAP.get(raw_price)

    duration = raw.get("duration_minutes")
    if duration is None and raw.get("duration_hours") is not None:
        duration = int(raw["duration_hours"] * 60)

    # ------------------------------------------------------------------
    # Validate enum-constrained scalar fields
    # ------------------------------------------------------------------
    candidate: Candidate = {
        "content":          name,
        "category":         raw.get("category", "activity"),
        "tags":             validate_tags(raw.get("tags", []), name),
        "vibe":             _validate_enum_field(raw.get("vibe"),          VibeTag,         "vibe",          name),
        "price_tier":       _validate_enum_field(raw_price,                PriceTier,       "price_tier",    name),
        "neighborhood":     _validate_enum_field(raw.get("neighborhood"),   NeighborhoodTag, "neighborhood",  name),
        "indoor_outdoor":   _validate_enum_field(raw_io,                   IndoorOutdoor,   "indoor_outdoor", name),
        "source":           _validate_enum_field(raw.get("source"),        DataSource,      "source",        name),
        "duration_minutes": duration,
        "requires_booking": raw.get("requires_booking"),
        "seasonal_relevance": raw.get("seasonal_relevance"),
        "effort_level":     raw.get("effort_level"),
    }

    log.debug(
        "features | '%s' → tags=%s vibe=%s price=%s neighborhood=%s io=%s",
        name, candidate["tags"], candidate["vibe"],
        candidate["price_tier"], candidate["neighborhood"], candidate["indoor_outdoor"],
    )
    return candidate
