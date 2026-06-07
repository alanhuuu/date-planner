import logging
import math
from datetime import date, datetime

from tags import ActivityTag
from config import (
    DECAY_CONSTANTS,
    FEEDBACK_DECAY_DAYS,
    FIRST_WARM_BOOST,
    FIRST_WARM_THRESHOLD,
    OUTDOOR_IDEAL_MAX,
    OUTDOOR_IDEAL_MIN,
    OUTDOOR_UNCOMFORTABLE_ABOVE,
    OUTDOOR_UNCOMFORTABLE_BELOW,
    PROLONGED_RAIN_BOOST,
    PROLONGED_RAIN_DAYS,
    SCORING_WEIGHTS,
    TIME_WINDOW_AFFINITY,
    TIME_WINDOW_MISMATCH_PENALTY,
)
import preferences as prefs

log = logging.getLogger(__name__)

# Day-of-week affinity scores per activity tag. Keys use ActivityTag.value strings
# so they stay in sync with the tag vocabulary defined in tags.py.
_DOW_AFFINITY = {
    ActivityTag.RESTAURANT.value:   {"monday": 0.5, "tuesday": 0.5, "wednesday": 0.6, "thursday": 0.7, "friday": 1.0, "saturday": 1.0, "sunday": 0.8},
    ActivityTag.LIVE_MUSIC.value:   {"monday": 0.3, "tuesday": 0.3, "wednesday": 0.5, "thursday": 0.7, "friday": 1.0, "saturday": 1.0, "sunday": 0.5},
    ActivityTag.COMEDY_SHOW.value:  {"monday": 0.3, "tuesday": 0.4, "wednesday": 0.5, "thursday": 0.6, "friday": 1.0, "saturday": 1.0, "sunday": 0.5},
    ActivityTag.COCKTAIL_BAR.value: {"monday": 0.3, "tuesday": 0.3, "wednesday": 0.5, "thursday": 0.6, "friday": 1.0, "saturday": 1.0, "sunday": 0.5},
    ActivityTag.WINE_BAR.value:     {"monday": 0.3, "tuesday": 0.4, "wednesday": 0.5, "thursday": 0.6, "friday": 0.9, "saturday": 1.0, "sunday": 0.6},
    ActivityTag.MUSEUM.value:       {"monday": 0.4, "tuesday": 0.6, "wednesday": 0.6, "thursday": 0.6, "friday": 0.7, "saturday": 0.9, "sunday": 0.9},
    ActivityTag.ART_GALLERY.value:  {"monday": 0.4, "tuesday": 0.6, "wednesday": 0.6, "thursday": 0.6, "friday": 0.7, "saturday": 0.9, "sunday": 0.9},
    ActivityTag.MARKET.value:       {"monday": 0.2, "tuesday": 0.3, "wednesday": 0.4, "thursday": 0.5, "friday": 0.6, "saturday": 1.0, "sunday": 0.9},
    ActivityTag.HIKING.value:       {"monday": 0.3, "tuesday": 0.3, "wednesday": 0.3, "thursday": 0.3, "friday": 0.6, "saturday": 1.0, "sunday": 1.0},
    ActivityTag.CYCLING.value:      {"monday": 0.3, "tuesday": 0.3, "wednesday": 0.3, "thursday": 0.3, "friday": 0.5, "saturday": 1.0, "sunday": 1.0},
    ActivityTag.PICNIC.value:       {"monday": 0.2, "tuesday": 0.2, "wednesday": 0.3, "thursday": 0.3, "friday": 0.5, "saturday": 1.0, "sunday": 1.0},
    ActivityTag.BRUNCH.value:       {"monday": 0.3, "tuesday": 0.3, "wednesday": 0.3, "thursday": 0.3, "friday": 0.5, "saturday": 0.9, "sunday": 1.0},
    ActivityTag.ROOFTOP.value:      {"monday": 0.3, "tuesday": 0.3, "wednesday": 0.4, "thursday": 0.5, "friday": 0.9, "saturday": 1.0, "sunday": 0.6},
}


def normalize(value, min_value, max_value):
    if max_value == min_value:
        return 0.0
    return (value - min_value) / (max_value - min_value)


def compute_recency_decay(last_seen_date, half_life_days):
    """Returns value in [0, 1]: 1.0 = seen today (most stale), 0.0 = never seen (perfectly fresh)."""
    if last_seen_date is None:
        return 0.0
    if isinstance(last_seen_date, datetime):
        last_seen_date = last_seen_date.date()
    lam = math.log(2) / half_life_days
    t = (date.today() - last_seen_date).days
    return math.exp(-lam * t)


def _novelty_score(candidate, category_log):
    """
    novelty = 1 - max(recency_decay(tag)) across all known tags.
    Tags never seen → decay 0 → candidate is maximally novel.
    Tags seen recently → decay near 1 → candidate is stale.
    """
    tags = candidate.get("tags", [])
    if not tags:
        return 0.5

    max_decay = 0.0
    for tag in tags:
        half_life = DECAY_CONSTANTS.get(tag)
        if half_life is None:
            continue
        entry = (category_log or {}).get(tag)
        last_seen = entry["last_suggested"] if entry else None
        decay = compute_recency_decay(last_seen, half_life)
        if decay > max_decay:
            max_decay = decay
            log.debug("  novelty | tag=%s last_seen=%s decay=%.3f", tag, last_seen, decay)

    score = 1.0 - max_decay
    log.debug("  novelty | max_decay=%.3f → score=%.3f", max_decay, score)
    return score


def _preference_score(candidate):
    """
    Average preference weight across all matched dimensions (cuisine, activity,
    vibe, neighborhood, price tier, indoor/outdoor). Normalized to [0, 1].
    """
    scores = []
    tags = candidate.get("tags", [])

    for tag in tags:
        if tag in prefs.CUISINE_WEIGHTS:
            scores.append(("cuisine", tag, prefs.CUISINE_WEIGHTS[tag]))
        if tag in prefs.ACTIVITY_WEIGHTS:
            scores.append(("activity", tag, prefs.ACTIVITY_WEIGHTS[tag]))

    vibe = candidate.get("vibe")
    if vibe and vibe in prefs.VIBE_WEIGHTS:
        scores.append(("vibe", vibe, prefs.VIBE_WEIGHTS[vibe]))

    neighborhood = candidate.get("neighborhood")
    if neighborhood and neighborhood in prefs.NEIGHBORHOOD_WEIGHTS:
        scores.append(("neighborhood", neighborhood, prefs.NEIGHBORHOOD_WEIGHTS[neighborhood]))

    price_tier = candidate.get("price_tier")
    if price_tier and price_tier in prefs.PRICE_WEIGHTS:
        scores.append(("price", price_tier, prefs.PRICE_WEIGHTS[price_tier]))

    io = candidate.get("indoor_outdoor")
    if io and io in prefs.INDOOR_OUTDOOR_PREFERENCE:
        scores.append(("indoor_outdoor", io, prefs.INDOOR_OUTDOOR_PREFERENCE[io]))

    for dim, key, val in scores:
        log.debug("  preference | %s=%s weight=%.2f", dim, key, val)

    if not scores:
        return 0.5

    raw = sum(v for _, _, v in scores) / len(scores)
    normalized = (raw + 1.0) / 2.0  # shift from [-1, 1] → [0, 1]
    log.debug("  preference | raw_avg=%.3f → score=%.3f", raw, normalized)
    return normalized


def _weather_score(candidate, weather):
    """
    Continuous score based on temperature comfort band, precipitation probability,
    first-warm-day trend boost, and prolonged-rain indoor boost.

    weather keys: temp_c, precip_prob (0–1), recent_avg_temp_c, consecutive_rain_days
    """
    if weather is None:
        return 0.5

    io            = candidate.get("indoor_outdoor", "both")
    temp          = weather.get("temp_c", 15.0)
    precip        = weather.get("precip_prob", 0.0)
    recent_avg    = weather.get("recent_avg_temp_c", temp)
    rain_days     = weather.get("consecutive_rain_days", 0)

    if io == "indoor":
        score = 0.8
        if rain_days >= PROLONGED_RAIN_DAYS:
            score = min(1.0, score * PROLONGED_RAIN_BOOST)
            log.debug("  weather | indoor + prolonged rain → score=%.3f", score)
        else:
            log.debug("  weather | indoor → score=%.3f", score)
        return score

    # Outdoor / both: temperature comfort
    if temp < OUTDOOR_UNCOMFORTABLE_BELOW or temp > OUTDOOR_UNCOMFORTABLE_ABOVE:
        temp_score = 0.1
    elif OUTDOOR_IDEAL_MIN <= temp <= OUTDOOR_IDEAL_MAX:
        temp_score = 1.0
    elif temp < OUTDOOR_IDEAL_MIN:
        temp_score = (temp - OUTDOOR_UNCOMFORTABLE_BELOW) / (OUTDOOR_IDEAL_MIN - OUTDOOR_UNCOMFORTABLE_BELOW)
    else:
        temp_score = (OUTDOOR_UNCOMFORTABLE_ABOVE - temp) / (OUTDOOR_UNCOMFORTABLE_ABOVE - OUTDOOR_IDEAL_MAX)

    temp_score = max(0.0, min(1.0, temp_score))
    precip_score = 1.0 - precip
    score = 0.6 * temp_score + 0.4 * precip_score

    log.debug(
        "  weather | temp=%.1f temp_score=%.3f precip=%.2f precip_score=%.3f base=%.3f",
        temp, temp_score, precip, precip_score, score,
    )

    if (temp - recent_avg) >= FIRST_WARM_THRESHOLD:
        score = min(1.0, score * FIRST_WARM_BOOST)
        log.debug("  weather | first-warm-day boost → score=%.3f", score)

    if rain_days >= PROLONGED_RAIN_DAYS and io == "outdoor":
        score *= 0.5
        log.debug("  weather | prolonged rain outdoor penalty → score=%.3f", score)

    return max(0.0, min(1.0, score))


def _temporal_score(candidate, current_dt):
    """
    0.5 × day-of-week relevance  +  0.5 × time-of-day window fit.
    Candidates that match the current window tag get 1.0; mismatches get TIME_WINDOW_MISMATCH_PENALTY.
    """
    dow  = current_dt.strftime("%A").lower()
    hour = current_dt.hour
    tags = candidate.get("tags", [])

    dow_scores = [_DOW_AFFINITY[t][dow] for t in tags if t in _DOW_AFFINITY]
    dow_score  = sum(dow_scores) / len(dow_scores) if dow_scores else 0.5
    log.debug("  temporal | dow=%s dow_score=%.3f (from tags %s)", dow, dow_score, [t for t in tags if t in _DOW_AFFINITY])

    current_window = next(
        (cfg for cfg in TIME_WINDOW_AFFINITY.values() if cfg["hours"][0] <= hour < cfg["hours"][1]),
        None,
    )

    if current_window is None:
        time_score = 0.5  # outside all defined windows (e.g. 0–9 am)
        log.debug("  temporal | hour=%d outside all windows → time_score=0.5", hour)
    elif any(t in current_window["tags"] for t in tags):
        time_score = 1.0
        log.debug("  temporal | hour=%d in window, tag match → time_score=1.0", hour)
    else:
        time_score = TIME_WINDOW_MISMATCH_PENALTY
        log.debug("  temporal | hour=%d in window, no tag match → time_score=%.2f", hour, TIME_WINDOW_MISMATCH_PENALTY)

    score = 0.5 * dow_score + 0.5 * time_score
    log.debug("  temporal | final=%.3f", score)
    return score


def _diversity_score(candidate, recent_suggestions):
    """
    Fraction of recent suggestions that differ from this candidate across
    vibe, price_tier, and neighborhood. 1.0 = completely fresh on all axes.
    """
    if not recent_suggestions:
        return 1.0

    n = len(recent_suggestions)

    def axis_diversity(key):
        value = candidate.get(key)
        if value is None:
            return 0.5
        diffs = sum(1 for s in recent_suggestions if s.get(key) != value)
        return diffs / n

    vibe_div  = axis_diversity("vibe")
    price_div = axis_diversity("price_tier")
    nbhd_div  = axis_diversity("neighborhood")
    score     = (vibe_div + price_div + nbhd_div) / 3.0

    log.debug(
        "  diversity | vibe=%.2f price=%.2f neighborhood=%.2f → score=%.3f",
        vibe_div, price_div, nbhd_div, score,
    )
    return score


def _feedback_score(candidate, feedback_rows):
    """
    Recency-weighted average of explicit ratings for suggestions with overlapping
    tags or the same category. Normalized from [-1, 1] → [0, 1]; 0.5 = neutral.

    feedback_rows: list of {rating: float, created_at: datetime, tags: list, category: str}
    """
    if not feedback_rows:
        return 0.5

    candidate_tags     = set(candidate.get("tags", []))
    candidate_category = candidate.get("category")
    today              = date.today()
    weighted_sum       = 0.0
    weight_total       = 0.0

    for row in feedback_rows:
        row_tags     = set(row.get("tags") or [])
        row_category = row.get("category")

        if not (row_tags & candidate_tags) and row_category != candidate_category:
            continue

        created_at = row.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.date()
        days_ago = (today - created_at).days if created_at else FEEDBACK_DECAY_DAYS

        recency_weight = math.exp(-days_ago / FEEDBACK_DECAY_DAYS)
        rating         = row.get("rating", 0.0)

        log.debug(
            "  feedback | rating=%.1f days_ago=%d recency_weight=%.3f",
            rating, days_ago, recency_weight,
        )
        weighted_sum  += recency_weight * rating
        weight_total  += recency_weight

    if weight_total == 0.0:
        return 0.5

    raw   = weighted_sum / weight_total
    score = (raw + 1.0) / 2.0
    log.debug("  feedback | weighted_avg=%.3f → score=%.3f", raw, score)
    return score


def compute_score(candidate, *, category_log=None, recent_suggestions=None, weather=None, feedback_rows=None, now=None):
    """
    Returns a dict of individual signal scores plus the weighted 'final' score.

    candidate         — feature-extracted dict (see engine/features.py)
    category_log      — {tag: {"last_suggested": date, ...}} from db/queries.get_category_log
    recent_suggestions — list of recent suggestion dicts (for diversity)
    weather           — {temp_c, precip_prob, recent_avg_temp_c, consecutive_rain_days}
    feedback_rows     — list of {rating, created_at, tags, category}
    now               — datetime override (defaults to datetime.now())
    """
    if now is None:
        now = datetime.now()

    name = candidate.get("content", candidate.get("category", "unknown"))
    log.debug("scoring candidate: %s", name)

    signals = {
        "novelty":    _novelty_score(candidate, category_log),
        "preference": _preference_score(candidate),
        "weather":    _weather_score(candidate, weather),
        "temporal":   _temporal_score(candidate, now),
        "diversity":  _diversity_score(candidate, recent_suggestions or []),
        "feedback":   _feedback_score(candidate, feedback_rows or []),
    }

    weight_sum = sum(SCORING_WEIGHTS[name] for name in signals)
    final = sum(SCORING_WEIGHTS[sig] * score for sig, score in signals.items()) / weight_sum

    log.debug(
        "scores for '%s': novelty=%.3f preference=%.3f weather=%.3f "
        "temporal=%.3f diversity=%.3f feedback=%.3f → final=%.3f",
        name,
        signals["novelty"], signals["preference"], signals["weather"],
        signals["temporal"], signals["diversity"], signals["feedback"],
        final,
    )

    signals["final"] = final
    return signals
