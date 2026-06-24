from datetime import datetime

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
        56: "bi-cloud-drizzle",
        57: "bi-cloud-drizzle",
        61: "bi-cloud-rain",
        63: "bi-cloud-rain",
        65: "bi-cloud-rain",
        66: "bi-cloud-rain",
        67: "bi-cloud-rain",
        71: "bi-snow",
        73: "bi-snow",
        75: "bi-snow",
        77: "bi-snow",
        80: "bi-cloud-rain",
        81: "bi-cloud-rain",
        82: "bi-cloud-rain",
        85: "bi-snow",
        86: "bi-snow",
        95: "bi-cloud-lightning-rain",
        96: "bi-cloud-lightning-rain",
        99: "bi-cloud-lightning-rain",
    }

    @classmethod
    def _map_icon(cls, code):
        if code is None:
            return "bi-cloud"
        return cls.WMO_MAP.get(code, "bi-cloud")

    @classmethod
    def _nearest_hour_index(cls, times, target_iso):
        try:
            target_dt = datetime.fromisoformat(target_iso)
            best_idx = 0
            min_diff = None
            for idx, t_str in enumerate(times):
                t_dt = datetime.fromisoformat(t_str)
                diff = abs((t_dt - target_dt).total_seconds())
                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    best_idx = idx
            return best_idx
        except Exception:
            return 0

    @classmethod
    def get_weather(cls):
        now = datetime.now()

        if (
            cls._cache
            and cls._last_update
            and (now - cls._last_update).total_seconds() < 1800
        ):
            return cls._cache

        try:
            lat = current_app.config.get("WEATHER_LAT", 52.237)
            lon = current_app.config.get("WEATHER_LON", 21.012)

            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&daily=weathercode,temperature_2m_max,windspeed_10m_max"
                f"&hourly=temperature_2m,weathercode,windspeed_10m"
                f"&timezone=auto"
            )

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            daily = data.get("daily", {})
            hourly = data.get("hourly", {})
            current = data.get("current_weather")

            daily_times = daily.get("time", [])
            daily_codes = daily.get("weathercode", [])
            daily_temps = daily.get("temperature_2m_max", [])
            daily_winds = daily.get("windspeed_10m_max", [])

            forecast = []
            dni_pl = ["Pon", "Wto", "Śro", "Czw", "Pią", "Sob", "Nied"]

            for i in range(min(len(daily_times), 5)):
                date_str = daily_times[i]
                dt = datetime.fromisoformat(date_str)

                if i == 0:
                    day_label = "Dziś"
                elif i == 1:
                    day_label = "Jutro"
                else:
                    day_label = dni_pl[dt.weekday()]

                daily_code = daily_codes[i] if i < len(daily_codes) else None
                daily_temp = daily_temps[i] if i < len(daily_temps) else None
                daily_wind = daily_winds[i] if i < len(daily_winds) else None

                code = daily_code
                temp = daily_temp or 0
                wind = daily_wind or 0

                if i == 0 and hourly and not current:
                    hourly_times = hourly.get("time", [])
                    idx = cls._nearest_hour_index(
                        hourly_times,
                        now.replace(minute=0, second=0, microsecond=0).isoformat(),
                    )
                    try:
                        code = hourly.get("weathercode", [None])[idx]
                        temp = hourly.get("temperature_2m", [temp])[idx]
                        wind = hourly.get("windspeed_10m", [wind])[idx]
                    except (IndexError, TypeError) as e:
                        current_app.logger.warning(
                            f"Failed to extract hourly data at index {idx}: {e}"
                        )

                forecast.append(
                    {
                        "day": day_label,
                        "temp": round(float(temp)) if temp is not None else None,
                        "wind": round(float(wind)) if wind is not None else None,
                        "icon": cls._map_icon(code),
                    }
                )

            # Lead Architect Fix: Map flat list to frontend strict contract shape
            weather_contract = {
                "today": (
                    forecast[0]
                    if forecast
                    else {"day": "Dziś", "temp": 0, "wind": 0, "icon": "bi-cloud"}
                ),
                "future": forecast[1:] if len(forecast) > 1 else [],
            }

            cls._cache = weather_contract
            cls._last_update = now
            return cls._cache

        except Exception as e:
            current_app.logger.error(f"Weather fetch error: {str(e)}")

            # Graceful degradation UI fallback matching display.js schema
            safe_fallback = {
                "today": {
                    "day": "Dziś",
                    "temp": "--",
                    "wind": "--",
                    "icon": "bi-cloud-slash",
                },
                "future": [
                    {
                        "day": "Jutro",
                        "temp": "--",
                        "wind": "--",
                        "icon": "bi-cloud-slash",
                    },
                    {
                        "day": "Pojutrze",
                        "temp": "--",
                        "wind": "--",
                        "icon": "bi-cloud-slash",
                    },
                ],
            }
            return cls._cache or safe_fallback
