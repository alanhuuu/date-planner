# Runtime schema for normalized candidates. Source-specific normalization lives
# in engine/features.py; the scoring engine receives model_dump(mode="json").

import logging

from pydantic import BaseModel, Field, ValidationError, ValidationInfo, ValidatorFunctionWrapHandler, field_validator

from tags import ALL_KNOWN_TAGS, TAG_FIELD_BY_VALUE, Category, DataSource, EffortLevel, IndoorOutdoor, NeighborhoodTag, PriceTier, VibeTag

log = logging.getLogger(__name__)


class Candidate(BaseModel):
    """Validate candidates, logging and defaulting invalid optional metadata.

    Unknown source fields are ignored. Invalid identity, category, or tag container
    types raise ValidationError; unknown or misplaced tags are dropped with a warning.
    """

    content: str
    category: Category = Category.ACTIVITY
    tags: list[str] = Field(default_factory=list)

    vibe: VibeTag | None = None
    price_tier: PriceTier | None = None
    neighborhood: NeighborhoodTag | None = None
    indoor_outdoor: IndoorOutdoor | None = None
    source: DataSource | None = None

    duration_minutes: int | None = Field(default=None, gt=0)
    requires_booking: bool | None = None
    seasonal_relevance: float | None = Field(default=None, ge=0, le=1)
    effort_level: EffortLevel | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str], info: ValidationInfo) -> list[str]:
        clean = []
        for tag in tags:
            normalized = tag.strip().lower()
            if normalized in ALL_KNOWN_TAGS:
                clean.append(normalized)
            elif normalized in TAG_FIELD_BY_VALUE:
                log.warning(
                    "candidate '%s': misplaced tag '%s' dropped — use the %s field",
                    info.data.get("content", "unknown"), tag, TAG_FIELD_BY_VALUE[normalized],
                )
            else:
                log.warning(
                    "candidate '%s': unknown tag '%s' dropped — add to tags.py if permanent",
                    info.data.get("content", "unknown"), tag,
                )
        return clean

    @field_validator(
        "vibe", "price_tier", "neighborhood", "indoor_outdoor",
        "source", "duration_minutes", "requires_booking", "seasonal_relevance",
        "effort_level", mode="wrap",
    )
    @classmethod
    def default_invalid_metadata(
        cls, value: object, handler: ValidatorFunctionWrapHandler, info: ValidationInfo,
    ) -> object:
        # Let Pydantic validate types, enums, and bounds before applying our
        # existing soft-failure policy for incomplete external data.
        try:
            return handler(value)
        except ValidationError:
            log.warning(
                "candidate '%s': invalid %s=%r — setting to None",
                info.data.get("content", "unknown"), info.field_name, value,
            )
            return None
