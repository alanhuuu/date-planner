from tags import Category, PriceTier, VibeTag


def load_seeds():
    return [
        {
        "name": "alan_home",
        "category": Category.ACTIVITY.value,
        "description": "Staying in and having a cozy night at home. Could involve cooking together, watching a movie, or just relaxing.",
        "neighborhood": "home",
        "price_tier": PriceTier.BUDGET.value,
        "indoor": True,
        "duration_hours": 4.0,
        "vibe": VibeTag.RELAXING.value,
        "tags": [],
        "energy_level": 1,
        "weather_sensitive": False,
        },

        {
        "name": "alexa_home",
        "category": Category.ACTIVITY.value,
        "description": "Staying in and having a cozy night at home. Could involve cooking together, watching a movie, or just relaxing.",
        "neighborhood": "home",
        "price_tier": PriceTier.BUDGET.value,
        "indoor": True,
        "duration_hours": 4.0,
        "vibe": VibeTag.RELAXING.value,
        "tags": [],
        "energy_level": 1,
        "weather_sensitive": False,
        },
    ]
