import json
from datetime import date

import requests_cache


def fetch_weather(target_date=None):
    if target_date is None:
        target_date = date.today()

    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 45.5088,
        "longitude": -73.5878,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "weather_code",
            "snowfall_sum",
        ],
        "models": "gem_seamless",
        "timezone": "America/Toronto",
        "past_days": 3,
    }

    data = cache_session.get(url, params=params).json()
    daily = data["daily"]
    dates = daily["time"]
    target_str = target_date.isoformat()

    if target_str not in dates:
        raise ValueError(f"Target date {target_str} not in API response")

    idx = dates.index(target_str)
    today = date.today()

    # Only actual past days — range(idx) can include future forecast dates if target_date is ahead of today
    preceding_days = [
        {
            "date": dates[i],
            "temperature_max": daily["temperature_2m_max"][i],
            "temperature_min": daily["temperature_2m_min"][i],
            "precipitation_sum": daily["precipitation_sum"][i],
        }
        for i in range(idx)
        if date.fromisoformat(dates[i]) < today
    ]

    consecutive_rain_days = 0
    for day in reversed(preceding_days):
        if (day["precipitation_sum"] or 0) > 0:
            consecutive_rain_days += 1
        else:
            break

    return {
        "target_date": target_str,
        "temperature_max": daily["temperature_2m_max"][idx],
        "temperature_min": daily["temperature_2m_min"][idx],
        "apparent_temperature_max": daily["apparent_temperature_max"][idx],
        "apparent_temperature_min": daily["apparent_temperature_min"][idx],
        "precipitation_sum": daily["precipitation_sum"][idx],
        "precipitation_probability_max": daily["precipitation_probability_max"][idx],
        "weather_code": daily["weather_code"][idx],
        "snowfall_sum": daily["snowfall_sum"][idx],
        "preceding_days": preceding_days,
        "consecutive_rain_days": consecutive_rain_days,
    }
