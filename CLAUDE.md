# Date Night Agent — CLAUDE.md

## What this is
A personal date planning assistant for Montreal. Delivers fresh, non-repetitive
date ideas, restaurant picks, and multi-part date plans via Telegram. Combines
a sophisticated deterministic scoring engine with a lightweight LLM agent layer
for generation and on-demand requests.

## Core constraints (non-negotiable)
- Zero recurring cost: Groq free tier, Open-Meteo, duckduckgo-search, Telegram Bot API
- Single Python process, no microservices
- SQLite only (db/models.py is the schema source of truth)
- All tunable parameters live in config.py — no magic numbers anywhere else
- All preference weights live in preferences.py
- Optimize for readability over cleverness — this is a learning project
- Log every scoring decision so the developer can understand why things rank

## Tech stack
- Python 3.11+
- LLM: Groq API (Llama 3.3 70B)
- DB: SQLite via SQLAlchemy
- Bot: python-telegram-bot
- Scheduler: APScheduler
- Search: duckduckgo-search + Eventbrite public API
- Weather: Open-Meteo (no key required)
- Agent: raw ReAct loop (no LangChain, no LangGraph)

## Architecture in one line
Raw candidates → Hard gates → Feature extraction → Multi-signal scoring →
Portfolio re-ranking → Agent layer (Groq) → Telegram delivery

---

## Layer 1 — Deterministic Engine (engine/)

This is the core intelligence. Runs entirely before the LLM sees anything.
Responsible for freshness, preference matching, and all scoring logic.

### Stage 1: Hard Gates (engine/gates.py)
Eliminates candidates that fail non-negotiable rules. A failed gate = score of 0.
- Cooldown not expired (per-category, configured in config.COOLDOWNS)
- Weather hard incompatibility (outdoor in heavy rain/snow/extreme cold)
- Hard preference filter violations (config via preferences.HARD_FILTERS)
- Dietary/accessibility violations (preferences.DIETARY_RESTRICTIONS)

### Stage 2: Feature Extraction (engine/features.py)
Tags every raw candidate dict with structured attributes before scoring.
Every candidate must have: category, vibe, price_tier, neighborhood,
indoor_outdoor, duration_minutes, requires_booking, seasonal_relevance,
effort_level, source, tags (list).

### Stage 3: Multi-Signal Scoring (engine/scoring.py)
Full formula:

    final_score = gate(candidate) * (
        w_novelty          * novelty_score()         +
        w_preference       * preference_score()      +
        w_weather          * weather_score()          +
        w_temporal         * temporal_score()         +
        w_diversity        * diversity_score()        +
        w_feedback         * feedback_score()         +
        w_duration_fit     * duration_fit_score()     +
        w_energy           * energy_score()           +
        w_novelty_gradient * novelty_gradient_score() +
        w_seasonal         * seasonal_score()         +
        w_source_quality   * source_quality_score()
    )

    # Post-score multipliers:
    * sequential_pattern_multiplier    (engine/reranker.py)
    * special_occasion_multiplier      (engine/reranker.py)
    * anti_fatigue_penalty             (engine/reranker.py)

All weights are in config.SCORING_WEIGHTS.

**novelty_score** — exponential decay per tag. Uses config.DECAY_CONSTANTS.
    novelty(tag) = e^(-days_since_last / lambda)
    candidate_novelty = 1 - max(novelty(t) for t in candidate.tags)

**preference_score** — weighted match against preferences.py profile.
    Cuisine, activity type, vibe, neighborhood, price tier, indoor/outdoor.

**weather_score** — continuous, not binary. Factors:
    - Current temperature vs OUTDOOR_IDEAL thresholds
    - Precipitation probability
    - Relative temperature trend (first warm day after cold = big outdoor boost)
    - Prolonged rain detection (boosts cozy indoor options)

**temporal_score** — relevance to current day/time context.
    - Day-of-week relevance matrix (romantic dinner on Friday = boost)
    - Time-of-day affinity windows from config.TIME_WINDOW_AFFINITY
    - Mismatch = config.TIME_WINDOW_MISMATCH_PENALTY

**diversity_score** — portfolio-level, not item-level.
    Scores how much this candidate adds to the diversity of recent suggestions
    across vibe, price tier, and neighborhood dimensions.

**feedback_score** — recency-weighted explicit + implicit signals.
    Explicit: thumbs up/down stored in feedback table.
    Implicit: suggestion shown but no feedback = mild negative signal.
    Completion rate per category tracked over last N suggestions.
    Uses config.FEEDBACK_DECAY_DAYS for recency weighting.

**duration_fit_score** — checks estimated duration against available time window.
    Uses config.DURATION_ESTIMATES_MINUTES + DURATION_BUFFER_MINUTES.
    Mismatch = config.DURATION_MISMATCH_PENALTY.

**energy_score** — effort level compatibility with current day type.
    Uses config.ENERGY_PROFILE (day → preferred effort) and
    config.ACTIVITY_EFFORT (tag → effort level).
    Mismatch delta > 0.4 = config.ENERGY_MISMATCH_PENALTY.

**novelty_gradient_score** — semantic distance from recent history centroid.
    Builds a feature vector for each candidate and computes distance from
    the centroid of the last NOVELTY_GRADIENT_WINDOW suggestions.
    High distance = NOVELTY_GRADIENT_BOOST. Low distance = NOVELTY_GRADIENT_PENALTY.

**seasonal_score** — Montreal event calendar awareness.
    During active festival periods (config.MONTREAL_SEASONAL_EVENTS),
    matching tags receive a boost multiplier.

**source_quality_score** — reliability weight of the data source.
    Uses config.SOURCE_QUALITY. Eventbrite > local blogs > DDG > TripAdvisor.

### Stage 4: Portfolio Re-ranking (engine/reranker.py)
Runs after scoring. Operates on the ranked candidate list as a whole.

- **Streak detection**: last STREAK_WINDOW suggestions all share a dimension
  (all indoor, all restaurant, all same neighborhood) → apply STREAK_BOOST
  to underrepresented dimensions.

- **Sequential pattern detection**: identifies good alternating patterns
  (preserve them) vs true monotony (break it). Uses PATTERN_WINDOW.

- **Diversity enforcement**: top N candidates must meet MIN_VIBE_DIVERSITY,
  MIN_PRICE_DIVERSITY, MIN_NEIGHBORHOOD_DIVERSITY thresholds.

- **Exploration injection**: at EXPLORATION_RATE probability, replace one
  top-N slot with a high-novelty candidate outside the preference profile.

- **Neighborhood exploration pressure**: every NEIGHBORHOOD_FORCE_EVERY_N
  suggestions, force one candidate from unexplored neighborhoods
  (not visited in NEIGHBORHOOD_EXPLORATION_DAYS).

- **Budget fatigue detection**: if last BUDGET_FATIGUE_WINDOW suggestions
  share the same price tier, boost underrepresented tiers.

- **Anti-fatigue penalty**: candidates that have scored top-3 more than
  ANTI_FATIGUE_THRESHOLD times without being selected get penalized.

- **Special occasion multiplier**: proximity to dates in SPECIAL_DATES
  boosts romantic + upscale scores in the lead-up window.

- **Complementary pairing**: used during multi-part date assembly.
  config.PAIRING_SCORES defines how well activity types pair sequentially.

---

## Layer 2 — Agent Layer (agent/)

Receives top N pre-scored candidates from the deterministic layer.
Uses a raw ReAct loop: Think → Act (call tool) → Observe → Think → ...

**agent/loop.py** — ReAct implementation. Max REACT_MAX_ITERATIONS tool calls.
**agent/tools.py** — all tool definitions available to the agent.
**agent/prompts.py** — all system prompts and tool description strings.

### Available tools
- search_events(query, date_range) → raw event results
- search_restaurants(query, filters) → raw restaurant results
- get_weather(date) → structured weather object
- get_history(n) → last N suggestions with scores
- get_preferences() → full preference profile
- score_candidates(candidates) → runs deterministic layer, returns ranked list
- build_date_plan(components) → assembles multi-part date arc with pairing scores

### Agent responsibilities
- **Scheduled push**: select best candidate from scored list, write narrative
- **On-demand /ideas**: interpret freeform request, call tools, return recommendation
- **On-demand /plan [day]**: build coherent multi-part date (activity + dinner +
  optional evening), checking neighborhood coherence, timing, and pairing scores
- **On-demand /vibes [type]**: filter by vibe, return best match

---

## Project structure
date_agent/
├── CLAUDE.md
├── main.py                 # entry point — wires bot, scheduler, agent together
├── config.py               # all tunable parameters
├── preferences.py          # hardcoded preference profile
├── db/
│   ├── models.py           # SQLAlchemy models — schema source of truth
│   └── queries.py          # all DB read/write functions (no raw SQL elsewhere)
├── engine/
│   ├── gates.py            # hard filter logic
│   ├── features.py         # feature extraction and candidate tagging
│   ├── scoring.py          # full multi-signal scoring formula
│   ├── reranker.py         # portfolio re-ranking, all post-score logic
│   └── decay.py            # decay functions and novelty computation
├── agent/
│   ├── loop.py             # ReAct loop
│   ├── tools.py            # tool definitions
│   └── prompts.py          # all LLM prompts
├── sources/
│   ├── weather.py          # Open-Meteo client
│   ├── events.py           # Eventbrite + DDG event search
│   └── restaurants.py      # DDG restaurant search
├── bot/
│   ├── handlers.py         # Telegram command handlers
│   └── scheduler.py        # APScheduler push jobs
└── utils/
    └── logger.py           # structured logging

## Telegram commands
- /ideas — on-demand single recommendation
- /plan [day] — multi-part date plan (activity + dinner + optional evening)
- /vibes [low-key|adventurous|romantic|surprise] — vibe-filtered recommendation
- /feedback 👍 or 👎 — rate the last suggestion
- /history — last 5 suggestions
- /preferences — show current preference profile

## Scheduled push
- Friday 5pm: weekend recommendation (1 activity + 1 restaurant + 1 event if available)
- Monday morning digest (toggle via config.MONDAY_DIGEST_ENABLED)

## How to work with me
- Tell me which file or module to build next
- Write complete, runnable code — no placeholders unless I explicitly ask
- When a module depends on something not yet built, stub it minimally so current module runs
- After each module, show me exactly how to test it in isolation
- Flag any decision point where my preference would change the implementation
- Log scoring decisions verbosely — I want to see why things rank the way they do
- Never assume a decision; ask if something is ambiguous