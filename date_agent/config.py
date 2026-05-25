# config.py
# All tunable parameters for the date night agent.
# This is the only file you need to touch to adjust system behavior.
# No logic lives here — just constants and settings.

# ---------------------------------------------------------------------------
# GROQ
# ---------------------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_MAX_TOKENS = 1024
GROQ_TEMPERATURE = 0.7          # higher = more creative recommendations

# ---------------------------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"     # your personal chat ID with the bot

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///date_agent.db"
SEARCH_CACHE_TTL_HOURS = 6      # how long to cache search results

# ---------------------------------------------------------------------------
# SCORING WEIGHTS
# Must sum to 1.0. Adjust to prioritize what matters most.
#
# novelty          — how long since this category/tag was last suggested
# preference       — match against your taste profile in preferences.py
# weather          — compatibility with current + trend weather
# temporal         — day-of-week + time-of-day window fit
# diversity        — portfolio-level freshness (breaks streaks)
# feedback         — explicit thumbs up/down + implicit completion signals
# duration_fit     — does estimated duration fit available time window
# energy           — effort level vs day type (weekday vs weekend)
# novelty_gradient — vector distance from recent history (catches semantic similarity)
# seasonal         — Montreal event calendar boosts
# source_quality   — reliability weight of the data source
# ---------------------------------------------------------------------------
SCORING_WEIGHTS = {
    "novelty":          0.22,
    "preference":       0.18,
    "weather":          0.15,
    "temporal":         0.08,
    "diversity":        0.08,
    "feedback":         0.07,
    "duration_fit":     0.06,
    "energy":           0.06,
    "novelty_gradient": 0.06,
    "seasonal":         0.03,
    "source_quality":   0.01,
}

# ---------------------------------------------------------------------------
# DECAY CONSTANTS (lambda values, in days)
# Lower = faster decay = category becomes stale sooner
# Higher = slower decay = category stays fresh longer
# ---------------------------------------------------------------------------
DECAY_CONSTANTS = {
    "restaurant":        7,
    "activity":         21,
    "event":             3,
    "neighborhood":     14,
    "vibe_romantic":    10,
    "vibe_adventurous": 21,
    "vibe_chill":        5,
    "vibe_cultural":    14,
    "vibe_social":      10,
    "price_budget":      7,
    "price_mid":        10,
    "price_upscale":    21,
    "outdoor_summer":   14,
    "outdoor_winter":    5,
    "outdoor_shoulder": 10,
}

# ---------------------------------------------------------------------------
# COOLDOWN PERIODS (hard gates, in days)
# Candidate is eliminated entirely if its primary category was suggested
# within this window. Stricter than decay — this is a hard block.
# ---------------------------------------------------------------------------
COOLDOWNS = {
    "restaurant":    5,
    "activity":     10,
    "event":         1,
    "neighborhood":  7,
}

# ---------------------------------------------------------------------------
# EXPLORATION vs EXPLOITATION
# 0.0 = always exploit (safe picks), 1.0 = always explore (chaos)
# At exploration_rate probability, preference score is ignored entirely
# and the system surfaces high-novelty candidates outside your normal profile.
# ---------------------------------------------------------------------------
EXPLORATION_RATE = 0.20

# ---------------------------------------------------------------------------
# STREAK DETECTION
# If the last STREAK_WINDOW suggestions all share a dimension (all indoor,
# all restaurants, all same neighborhood) → apply inverse boost to break it.
# Good alternating patterns (budget/mid/budget/mid) are preserved.
# ---------------------------------------------------------------------------
STREAK_WINDOW = 4
STREAK_BOOST = 2.0

# ---------------------------------------------------------------------------
# SEQUENTIAL PATTERN DETECTION
# Looks beyond streaks — identifies alternating or cycling patterns and
# decides whether to reinforce (good pattern) or break (monotony).
# ---------------------------------------------------------------------------
PATTERN_WINDOW = 6              # how many suggestions to analyze for patterns
PATTERN_REINFORCE_THRESHOLD = 0.8   # similarity score above which pattern is "good"
PATTERN_BREAK_THRESHOLD = 0.9       # above this = monotony, force break

# ---------------------------------------------------------------------------
# PORTFOLIO DIVERSITY
# Top N candidates passed to the agent must span minimum distinct dimensions.
# ---------------------------------------------------------------------------
TOP_N_CANDIDATES = 5
MIN_VIBE_DIVERSITY = 2
MIN_PRICE_DIVERSITY = 2
MIN_NEIGHBORHOOD_DIVERSITY = 2

# ---------------------------------------------------------------------------
# WEATHER
# ---------------------------------------------------------------------------
MONTREAL_LAT = 45.5017
MONTREAL_LON = -73.5673
WEATHER_FORECAST_DAYS = 3
WEATHER_TREND_DAYS = 7          # days of history to compute relative temperature trend

# Temperature thresholds (Celsius)
OUTDOOR_IDEAL_MIN = 15
OUTDOOR_IDEAL_MAX = 28
OUTDOOR_UNCOMFORTABLE_BELOW = 5
OUTDOOR_UNCOMFORTABLE_ABOVE = 33

# Weather trend psychological modifiers
# "First warm weekend after cold stretch" → outdoor gets a strong bonus
FIRST_WARM_THRESHOLD = 10       # delta °C above recent average = "first warm"
FIRST_WARM_BOOST = 1.4          # multiplier on outdoor scores
PROLONGED_RAIN_DAYS = 3         # consecutive rainy days before "cozy indoor" kicks in
PROLONGED_RAIN_BOOST = 1.3      # multiplier on indoor/cozy scores

# ---------------------------------------------------------------------------
# TIME-OF-DAY AFFINITY
# Maps time windows (hour ranges) to activity types that fit naturally.
# Candidates outside the current window get a penalty multiplier.
# ---------------------------------------------------------------------------
TIME_WINDOW_AFFINITY = {
    "morning":   {"hours": (9, 12),  "tags": ["brunch", "market", "hiking", "cycling", "museum"]},
    "afternoon": {"hours": (12, 17), "tags": ["museum", "art_gallery", "activity", "picnic", "cycling"]},
    "evening":   {"hours": (17, 21), "tags": ["restaurant", "cocktail_bar", "wine_bar", "live_music", "show"]},
    "late":      {"hours": (21, 24), "tags": ["live_music", "comedy_show", "rooftop", "cocktail_bar", "jazz"]},
}
TIME_WINDOW_MISMATCH_PENALTY = 0.5   # multiplier applied to out-of-window candidates

# ---------------------------------------------------------------------------
# ENERGY / EFFORT SCORING
# Maps day type to preferred effort level. Scale: 0.0 (passive) to 1.0 (active).
# ---------------------------------------------------------------------------
ENERGY_PROFILE = {
    "monday":    0.2,
    "tuesday":   0.3,
    "wednesday": 0.3,
    "thursday":  0.4,
    "friday":    0.7,
    "saturday":  0.9,
    "sunday":    0.5,
}

# Effort level of activity tags (0.0 = passive, 1.0 = physically demanding)
ACTIVITY_EFFORT = {
    "hiking":        0.9,
    "cycling":       0.8,
    "kayaking":      0.8,
    "skating":       0.7,
    "dancing":       0.6,
    "food_tour":     0.4,
    "market":        0.3,
    "museum":        0.2,
    "art_gallery":   0.2,
    "restaurant":    0.1,
    "wine_bar":      0.1,
    "cocktail_bar":  0.1,
    "cinema":        0.1,
    "comedy_show":   0.1,
    "live_music":    0.2,
    "rooftop":       0.2,
}
ENERGY_MISMATCH_PENALTY = 0.6   # multiplier when effort delta > 0.4

# ---------------------------------------------------------------------------
# DURATION COMPATIBILITY
# ---------------------------------------------------------------------------
DURATION_ESTIMATES_MINUTES = {
    "restaurant":    90,
    "cocktail_bar":  60,
    "wine_bar":      75,
    "live_music":   150,
    "comedy_show":  120,
    "museum":       120,
    "art_gallery":   75,
    "hiking":       180,
    "cycling":      150,
    "market":        60,
    "festival":     240,
    "food_tour":    150,
    "cinema":       150,
    "escape_room":   90,
    "rooftop":       90,
}
DURATION_BUFFER_MINUTES = 30    # padding added to estimated duration
DURATION_MISMATCH_PENALTY = 0.4 # multiplier when candidate won't fit time window

# ---------------------------------------------------------------------------
# NOVELTY GRADIENT (vector distance from recent history)
# Measures semantic distance between a candidate and the centroid of
# recent suggestions. High distance = novelty bonus.
# ---------------------------------------------------------------------------
NOVELTY_GRADIENT_WINDOW = 5     # how many recent suggestions to form the centroid
NOVELTY_GRADIENT_BOOST = 1.3    # multiplier for candidates far from centroid
NOVELTY_GRADIENT_PENALTY = 0.7  # multiplier for candidates close to centroid

# ---------------------------------------------------------------------------
# FEEDBACK SIGNALS
# ---------------------------------------------------------------------------
FEEDBACK_DECAY_DAYS = 30        # older feedback matters less
IMPLICIT_NO_RESPONSE_PENALTY = 0.3   # suggestion shown, no feedback sent
COMPLETION_RATE_WINDOW = 10     # last N suggestions to compute completion rate per category

# ---------------------------------------------------------------------------
# ANTI-FATIGUE (perpetual runners-up penalty)
# Penalizes candidates that consistently score highly but never get selected.
# ---------------------------------------------------------------------------
ANTI_FATIGUE_THRESHOLD = 2      # times scored top-3 without selection before penalty
ANTI_FATIGUE_PENALTY = 0.8      # multiplier applied after threshold

# ---------------------------------------------------------------------------
# NEIGHBORHOOD EXPLORATION PRESSURE
# Forces systematic coverage of neighborhoods you haven't visited recently.
# ---------------------------------------------------------------------------
NEIGHBORHOOD_EXPLORATION_DAYS = 30  # days before a neighborhood is "unexplored"
NEIGHBORHOOD_FORCE_EVERY_N = 4      # every N suggestions, force one from unexplored

# ---------------------------------------------------------------------------
# BUDGET FATIGUE DETECTION
# Tracks spend tier patterns and rebalances if too monotonous.
# ---------------------------------------------------------------------------
BUDGET_FATIGUE_WINDOW = 3       # look at last N price tiers
BUDGET_FATIGUE_BOOST = 1.3      # boost underrepresented tiers after fatigue detected

# ---------------------------------------------------------------------------
# COMPLEMENTARY PAIRING SCORES
# Used when building multi-part dates. Scores how well two activity types
# pair together sequentially.
# ---------------------------------------------------------------------------
PAIRING_SCORES = {
    ("art_gallery",  "wine_bar"):        0.95,
    ("art_gallery",  "cocktail_bar"):    0.85,
    ("museum",       "restaurant"):      0.80,
    ("hiking",       "brunch"):          0.90,
    ("hiking",       "restaurant"):      0.85,
    ("cycling",      "brunch"):          0.85,
    ("market",       "picnic"):          0.95,
    ("market",       "restaurant"):      0.75,
    ("comedy_show",  "cocktail_bar"):    0.85,
    ("comedy_show",  "wine_bar"):        0.80,
    ("live_music",   "cocktail_bar"):    0.90,
    ("live_music",   "restaurant"):      0.75,
    ("rooftop",      "restaurant"):      0.70,
    ("food_tour",    "cocktail_bar"):    0.85,
    ("skating",      "hot_chocolate"):   0.95,
    ("skating",      "restaurant"):      0.80,
    ("museum",       "steakhouse"):      0.40,
    ("clubbing",     "fine_dining"):     0.30,
}
DEFAULT_PAIRING_SCORE = 0.55    # fallback for unlisted combinations

# ---------------------------------------------------------------------------
# SOURCE QUALITY WEIGHTS
# Reliability score of each data source. Higher = more trustworthy results.
# ---------------------------------------------------------------------------
SOURCE_QUALITY = {
    "eventbrite":   1.0,
    "mtl_blog":     0.85,
    "tourisme_mtl": 0.90,
    "ddg_search":   0.70,
    "tripadvisor":  0.50,
    "yelp":         0.55,
}

# ---------------------------------------------------------------------------
# MONTREAL SEASONAL EVENT CALENDAR
# During active festival periods, matching tags receive a score boost.
# Format: name → {months, boost_tags, boost_multiplier}
# ---------------------------------------------------------------------------
MONTREAL_SEASONAL_EVENTS = {
    "jazz_festival": {
        "months": [6, 7],
        "boost_tags": ["live_music", "jazz", "outdoor", "festival", "cultural"],
        "boost_multiplier": 1.5,
    },
    "just_for_laughs": {
        "months": [7],
        "boost_tags": ["comedy_show", "festival", "live_performance"],
        "boost_multiplier": 1.5,
    },
    "osheaga": {
        "months": [8],
        "boost_tags": ["concert", "festival", "outdoor", "live_music"],
        "boost_multiplier": 1.4,
    },
    "igloofest": {
        "months": [1, 2],
        "boost_tags": ["outdoor", "music", "winter", "festival"],
        "boost_multiplier": 1.4,
    },
    "montreal_en_lumiere": {
        "months": [2, 3],
        "boost_tags": ["food", "cultural", "winter", "restaurant"],
        "boost_multiplier": 1.3,
    },
    "nuit_blanche": {
        "months": [3],
        "boost_tags": ["cultural", "art_gallery", "late_night", "free"],
        "boost_multiplier": 1.6,
    },
    "terrasses_season": {
        "months": [5, 6, 7, 8, 9],
        "boost_tags": ["rooftop", "patio", "outdoor", "cocktail_bar"],
        "boost_multiplier": 1.3,
    },
    "jean_talon_peak": {
        "months": [7, 8, 9],
        "boost_tags": ["market", "outdoor", "food_tour"],
        "boost_multiplier": 1.2,
    },
}

# ---------------------------------------------------------------------------
# SPECIAL OCCASION PROXIMITY
# Boosts romantic + upscale options in the lead-up to special dates.
# Format: "MM-DD": "label"
# ---------------------------------------------------------------------------
SPECIAL_DATES = {
    # "02-14": "Valentine's Day",
    # "MM-DD": "Anniversary",
}
SPECIAL_OCCASION_LEAD_DAYS = 7      # start boosting N days before
SPECIAL_OCCASION_BOOST = 1.5        # multiplier on romantic + upscale scores

# ---------------------------------------------------------------------------
# SEASONS (Montreal-specific)
# ---------------------------------------------------------------------------
WINTER_MONTHS = [11, 12, 1, 2, 3]
SHOULDER_MONTHS = [4, 5, 9, 10]
SUMMER_MONTHS = [6, 7, 8]

# ---------------------------------------------------------------------------
# SCHEDULER
# ---------------------------------------------------------------------------
PUSH_DAY = "friday"
PUSH_HOUR = 17
PUSH_MINUTE = 0
MONDAY_DIGEST_ENABLED = False
MONDAY_DIGEST_HOUR = 9

# ---------------------------------------------------------------------------
# AGENT
# ---------------------------------------------------------------------------
REACT_MAX_ITERATIONS = 6
AGENT_TIMEOUT_SECONDS = 30