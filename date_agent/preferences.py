# preferences.py
# Your hardcoded preference profile.
# Values range from -1.0 (hate) to 1.0 (love).
# 0.0 = neutral, negative values = active avoidance.
#
# The scoring engine uses these weights when matching candidates against
# your profile. Update these freely — they're just numbers.
#
# String keys in this file must match values defined in date_agent/tags.py.
# Quick reference: CUISINE_WEIGHTS → tags.CuisineTag, ACTIVITY_WEIGHTS → tags.ActivityTag,
# VIBE_WEIGHTS → tags.VibeTag, NEIGHBORHOOD_WEIGHTS → tags.NeighborhoodTag,
# PRICE_WEIGHTS → tags.PriceTier, INDOOR_OUTDOOR_PREFERENCE → tags.IndoorOutdoor,
# HARD_FILTERS → tags.ActivityTag / tags.GenericTag.

# ---------------------------------------------------------------------------
# CUISINE PREFERENCES
# Used to score restaurant candidates.
# ---------------------------------------------------------------------------
CUISINE_WEIGHTS = {
    "japanese":         0.9,
    "korean":           0.8,
    "french":           0.8,
    "italian":          0.7,
    "mediterranean":    0.7,
    "thai":             0.7,
    "vietnamese":       0.8,
    "mexican":          0.6,
    "peruvian":         0.8,
    "middle_eastern":   0.7,
    "indian":           0.5,
    "greek":            0.6,
    "spanish":          0.7,
    "seafood":          0.7,
    "steakhouse":       0.5,
    "brunch":           0.8,
    "fast_food":       -0.8,
    "buffet":          -0.5,
}

# ---------------------------------------------------------------------------
# ACTIVITY TYPE PREFERENCES
# Used to score activity and event candidates.
# ---------------------------------------------------------------------------
ACTIVITY_WEIGHTS = {
    "art_gallery":          0.7,
    "museum":               0.7,
    "live_music":           0.9,
    "comedy_show":          0.8,
    "theatre":              0.6,
    "cinema":               0.6,
    "concert":              0.9,
    "rooftop":              0.8,
    "hiking":               0.7,
    "cycling":              0.7,
    "kayaking":             0.8,
    "skating":              0.7,     # Montreal winter activity
    "skiing":               0.6,
    "picnic":               0.8,
    "market":               0.7,     # Jean-Talon, Atwater, etc.
    "festival":             0.9,
    "food_tour":            0.8,
    "cooking_class":        0.7,
    "escape_room":          0.5,
    "bowling":              0.4,
    "mini_golf":            0.4,
    "spa":                  0.6,
    "sports_game":          0.5,
    "club_nightlife":      -0.3,
    "tourist_trap":        -0.9,
}

# ---------------------------------------------------------------------------
# VIBE PREFERENCES
# ---------------------------------------------------------------------------
VIBE_WEIGHTS = {
    "romantic":     0.9,
    "adventurous":  0.7,
    "chill":        0.6,
    "cultural":     0.7,
    "social":       0.5,
    "novelty":      0.8,    # trying something new
    "cozy":         0.7,
}

# ---------------------------------------------------------------------------
# NEIGHBORHOOD PREFERENCES (Montreal)
# ---------------------------------------------------------------------------
NEIGHBORHOOD_WEIGHTS = {
    "mile_end":         0.9,
    "plateau":          0.9,
    "old_montreal":     0.7,
    "little_italy":     0.8,
    "griffintown":      0.7,
    "saint_henri":      0.8,
    "ndg":              0.6,
    "rosemont":         0.7,
    "villeray":         0.7,
    "hochelaga":        0.6,
    "downtown":         0.5,
    "chinatown":        0.5,
    "westmount":        0.5,
    "laval":           -0.3,
    "south_shore":     -0.3,
}

# ---------------------------------------------------------------------------
# PRICE TIER PREFERENCES
# ---------------------------------------------------------------------------
PRICE_WEIGHTS = {
    "budget":   0.5,    # fine, not exciting
    "mid":      0.9,    # sweet spot
    "upscale":  0.6,    # occasionally, for special nights
}

PRICE_CEILING = "upscale"   # never suggest anything above this

# ---------------------------------------------------------------------------
# HARD FILTERS
# Candidates matching any of these tags are eliminated entirely at the gate stage.
# Add strings that match tags in features.py.
# ---------------------------------------------------------------------------
HARD_FILTERS = [
    "chain",
    "tourist_trap",
]

# ---------------------------------------------------------------------------
# INDOOR / OUTDOOR PREFERENCE
# Baseline preference, overridden by weather scoring at runtime.
# ---------------------------------------------------------------------------
INDOOR_OUTDOOR_PREFERENCE = {
    "indoor":   0.5,
    "outdoor":  0.8,    # prefer outdoor when weather allows
    "both":     0.7,
}

# ---------------------------------------------------------------------------
# SPECIAL DATES
# The system will boost romantic + upscale suggestions in the week leading
# up to these dates. Format: "MM-DD"
# ---------------------------------------------------------------------------
SPECIAL_DATES = {
    "02-08": "Alexa's Birthday",
    "02-14": "Valentine's Day",
    "07-02": "Anniversary",
    "11-17": "Alan's Birthday",
}