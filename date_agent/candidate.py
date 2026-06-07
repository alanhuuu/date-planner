# candidate.py
# TypedDict defining the shape of every candidate dict flowing through the pipeline.
#
# Raw candidates from sources/ are unstructured dicts. engine/features.extract_features()
# normalizes them into this shape before scoring. Every field annotated with a comment
# names the Enum class in tags.py that constrains its valid values.
#
# TypedDict is used (vs dataclass) because the pipeline reads candidates via dict.get()
# throughout scoring.py — TypedDict is structurally compatible with no call-site changes.
# Fields use str | None (not Enum types) to avoid forcing Enum imports at every call site.
# Enforcement happens at validation time in engine/features.py, not here.

from __future__ import annotations
from typing import Optional, TypedDict


class Candidate(TypedDict, total=False):
    content:            str
    category:           str
    tags:               list[str]  # validated against tags.ALL_KNOWN_TAGS in features.py
    vibe:               Optional[str]   # tags.VibeTag value
    price_tier:         Optional[str]   # tags.PriceTier value
    neighborhood:       Optional[str]   # tags.NeighborhoodTag value
    indoor_outdoor:     Optional[str]  # tags.IndoorOutdoor value
    source:             Optional[str]   # tags.DataSource value
    duration_minutes:   Optional[int]
    requires_booking:   Optional[bool]
    seasonal_relevance: Optional[float]   # 0.0–1.0; set during feature extraction
    effort_level:       Optional[float]   # 0.0 (passive) → 1.0 (very active)
