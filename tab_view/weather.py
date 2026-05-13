from datetime import datetime, timedelta

import requests
from flask import current_app


class WeatherService:
    _cache = None
    _last_update = None

    WMO_MAP = {
        0: "bi-brightness-high",
        1: "bi-cloud-sun",
        2: "bi-cloud-sun",
        3: "bi-clouds",
        45: "bi-cloud-fog",
        48: "bi-cloud-fog",
        51: "bi-cloud-drizzle",
        53: "bi-cloud-drizzle",
        55: "bi-cloud-drizzle",
        61: "bi-cloud-rain",
        63: "bi-cloud-rain",
        65: "bi-cloud-rain",
        71: "bi-snow",
        73: "bi-snow",
        75: "bi-snow",
        95: "bi-cloud-lightning-rain",
    }

    @classmethod
    def get_weather(cls):
        now = datetime.now()
        cache_ttl = current_app.config.get("WEATHER_CACHE_MINUTES", 20)

        if (
            cls._cache
            and cls._last_update
            and (now - cls._last_update) < timedelta(minutes=cache_ttl)
        ):
            return cls._cache

        try:
            lat = current_app.config["WEATHER_LATITUDE"]
            lon = current_app.config["WEATHER_LONGITUDE"]
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,windspeed_10m_max&forecast_days=3&timezone=auto"

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json().get("daily", {})

            forecast = []
            for i in range(3):
                code = data["weathercode"][i]
                forecast.append(
                    {
                        "day": "Today"
                        if i == 0
                        else (datetime.now() + timedelta(days=i)).strftime("%a"),
                        "temp": round(data["temperature_2m_max"][i]),
                        "wind": round(data["windspeed_10m_max"][i]),
                        "icon": cls.WMO_MAP.get(code, "bi-cloud"),
                    }
                )

            cls._cache = forecast
            cls._last_update = now
            return cls._cache
        except Exception as e:
            current_app.logger.error(f"Weather fetch error: {str(e)}")
            return cls._cache or []
