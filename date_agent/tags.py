# tags.py
# Single source of truth for every tag string used in the pipeline.
#
# All Enums use the `str, Enum` mixin so that every member's .value is a plain
# string — they pass directly wherever a string is expected, and you can still
# look them up by value: ActivityTag("live_music") == ActivityTag.LIVE_MUSIC.
#
# To add a new tag, add it to the appropriate Enum class here and nowhere else.
# The soft validator in candidate.py will log a WARNING for any tag string
# that isn't registered here, so you'll notice quickly if something is missing.
#
# String keys in config.py and preferences.py must match values defined here.
# See DecayKey for DECAY_CONSTANTS keys, ActivityTag for ACTIVITY_EFFORT keys, etc.

from enum import Enum


# ---------------------------------------------------------------------------
# Candidate-level tags and attributes
# ---------------------------------------------------------------------------


class Category(str, Enum):
    """Primary candidate category. Used in COOLDOWNS and candidate.category field."""
    RESTAURANT = "restaurant"
    ACTIVITY   = "activity"
    EVENT      = "event"


class VibeTag(str, Enum):
    """Vibe/mood tags. Used in VIBE_WEIGHTS and candidate.vibe field."""
    ROMANTIC    = "romantic"
    ADVENTUROUS = "adventurous"
    CHILL       = "chill"
    CULTURAL    = "cultural"
    SOCIAL      = "social"
    NOVELTY     = "novelty"
    RELAXING    = "relaxing"


class PriceTier(str, Enum):
    """Price tier values. Used in PRICE_WEIGHTS and candidate.price_tier field."""
    BUDGET  = "budget"
    MID     = "mid"
    UPSCALE = "upscale"


class NeighborhoodTag(str, Enum):
    """Montreal neighborhood tags. Used in NEIGHBORHOOD_WEIGHTS and candidate.neighborhood field."""
    MILE_END     = "mile_end"
    PLATEAU      = "plateau"
    OLD_MONTREAL = "old_montreal"
    LITTLE_ITALY = "little_italy"
    GRIFFINTOWN  = "griffintown"
    SAINT_HENRI  = "saint_henri"
    NDG          = "ndg"
    ROSEMONT     = "rosemont"
    VILLERAY     = "villeray"
    HOCHELAGA    = "hochelaga"
    DOWNTOWN     = "downtown"
    CHINATOWN    = "chinatown"
    WESTMOUNT    = "westmount"
    LAVAL        = "laval"
    SOUTH_SHORE  = "south_shore"
    HOME         = "home"


class IndoorOutdoor(str, Enum):
    """Indoor/outdoor setting. Used in INDOOR_OUTDOOR_PREFERENCE and candidate.indoor_outdoor field."""
    INDOOR  = "indoor"
    OUTDOOR = "outdoor"
    BOTH_INDOOR_OUTDOOR    = "both_indoor_outdoor"


class DataSource(str, Enum):
    """Data source identifiers. Used in SOURCE_QUALITY and candidate.source field."""
    EVENTBRITE   = "eventbrite"
    MTL_BLOG     = "mtl_blog"
    TOURISME_MTL = "tourisme_mtl"
    DDG_SEARCH   = "ddg_search"
    TRIPADVISOR  = "tripadvisor"
    YELP         = "yelp"


class ActivityTag(str, Enum):
    """Activity and venue type tags. Used in ACTIVITY_WEIGHTS, ACTIVITY_EFFORT,
    DURATION_ESTIMATES_MINUTES, _DOW_AFFINITY, PAIRING_SCORES, and TIME_WINDOW_AFFINITY."""
    LIVE_MUSIC     = "live_music"
    COMEDY_SHOW    = "comedy_show"
    THEATRE        = "theatre"
    CINEMA         = "cinema"
    CONCERT        = "concert"
    HIKING         = "hiking"
    CYCLING        = "cycling"
    KAYAKING       = "kayaking"
    SKATING        = "skating"
    SKIING         = "skiing"
    PICNIC         = "picnic"
    FESTIVAL       = "festival"
    SPORTS_GAME    = "sports_game"
    BRUNCH         = "brunch"       # meal activity (also in CUISINE_WEIGHTS — same string, valid either way)
    RESTAURANT     = "restaurant"
    FINE_DINING    = "fine_dining"  # used in PAIRING_SCORES


class CuisineTag(str, Enum):
    """Cuisine type tags. Used in CUISINE_WEIGHTS for restaurant scoring."""
    JAPANESE       = "japanese"
    CHINESE        = "chinese"
    KOREAN         = "korean"
    FRENCH         = "french"
    ITALIAN        = "italian"
    MEDITERRANEAN  = "mediterranean"
    THAI           = "thai"
    VIETNAMESE     = "vietnamese"
    MEXICAN        = "mexican"
    MIDDLE_EASTERN = "middle_eastern"
    INDIAN         = "indian"
    GREEK          = "greek"
    SPANISH        = "spanish"
    SEAFOOD        = "seafood"
    STEAKHOUSE     = "steakhouse"
    FAST_FOOD      = "fast_food"
    BUFFET         = "buffet"


class GenericTag(str, Enum):
    """Cross-cutting labels used in boost_tags, HARD_FILTERS, seeds, and seasonal events.
    These don't belong exclusively to one category above."""
    OUTDOOR          = "outdoor"
    FOOD             = "food"
    MUSIC            = "music"
    WINTER           = "winter"
    FREE             = "free"
    LATE_NIGHT       = "late_night"
    PATIO            = "patio"
    LIVE_PERFORMANCE = "live_performance"
    CHAIN            = "chain"
    HOT_CHOCOLATE    = "hot_chocolate"  # used in PAIRING_SCORES
    SHOW             = "show"           # generic performance category in TIME_WINDOW_AFFINITY


class EffortLevel(int, Enum):
    """Discrete physical effort scale for candidates. Used in ACTIVITY_EFFORT and ENERGY_PROFILE.
    Replaces the float 0.0–1.0 scale with human-readable levels."""
    VERY_LOW  = 1  # passive: watching, listening, sitting at a bar
    LOW       = 2  # light: museum stroll, market visit, food tour
    MODERATE  = 3  # moderate: dancing, casual cycling on flat terrain
    HIGH      = 4  # active: cycling hills, skating, vigorous hiking
    VERY_HIGH = 5  # vigorous: backcountry hiking, kayaking, skiing


# ---------------------------------------------------------------------------
# Non-candidate-level identifiers (scoring infrastructure)
# ---------------------------------------------------------------------------


class DecayKey(str, Enum):
    """Keys used only in DECAY_CONSTANTS. These are scoring-infrastructure identifiers,
    NOT candidate-level tags — do not add them to candidate.tags lists."""
    RESTAURANT       = "restaurant"
    ACTIVITY         = "activity"
    EVENT            = "event"
    NEIGHBORHOOD     = "neighborhood"
    VIBE_ROMANTIC    = "vibe_romantic"
    VIBE_ADVENTUROUS = "vibe_adventurous"
    VIBE_CHILL       = "vibe_chill"
    VIBE_CULTURAL    = "vibe_cultural"
    VIBE_SOCIAL      = "vibe_social"
    PRICE_BUDGET     = "price_budget"
    PRICE_MID        = "price_mid"
    PRICE_UPSCALE    = "price_upscale"
    OUTDOOR_SUMMER   = "outdoor_summer"
    OUTDOOR_WINTER   = "outdoor_winter"
    OUTDOOR_SHOULDER = "outdoor_shoulder"


# ---------------------------------------------------------------------------
# Values with dedicated fields must never appear in candidate.tags, even if
# another enum also defines them (e.g. GenericTag.OUTDOOR).
# ---------------------------------------------------------------------------
TAG_FIELD_BY_VALUE: dict[str, str] = {
    member.value: field
    for field, enum_class in (
        ("category", Category), ("vibe", VibeTag), ("price_tier", PriceTier),
        ("neighborhood", NeighborhoodTag), ("indoor_outdoor", IndoorOutdoor),
        ("source", DataSource),
    )
    for member in enum_class
}

# Only cuisine, activity, and general labels without a dedicated field are tags.
ALL_KNOWN_TAGS: frozenset[str] = frozenset(
    tag.value
    for cls in (ActivityTag, CuisineTag, GenericTag)
    for tag in cls
    if tag.value not in TAG_FIELD_BY_VALUE
)
