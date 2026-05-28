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
        try:
            return cls.WMO_MAP.get(int(code), "bi-cloud")
        except (ValueError, TypeError):
            return "bi-cloud"

    @classmethod
    def _nearest_hour_index(cls, hourly_times, target_iso):
        """
        hourly_times: list of ISO time strings from API \
            (timezone already applied by API when timezone=auto)
        target_iso: ISO string like '2026-05-28T11:00'
        Returns index of nearest hour (int) or 0 if not found.
        """
        if not hourly_times:
            return 0
        try:
            best_idx = 0
            best_diff = None
            target = datetime.fromisoformat(target_iso)
            for i, t in enumerate(hourly_times):
                try:
                    dt = datetime.fromisoformat(t)
                except ValueError as e:
                    current_app.logger.warning(
                        f"Invalid isoformat in hourly_times '{t}': {e}"
                    )
                    continue
                diff = abs((dt - target).total_seconds())
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best_idx = i
            return best_idx
        except ValueError as e:
            current_app.logger.warning(f"Invalid target_iso format '{target_iso}': {e}")
            return 0

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

            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&daily=weathercode,temperature_2m_max,windspeed_10m_max"
                f"&hourly=weathercode,temperature_2m,windspeed_10m"
                f"&forecast_days=3&timezone=auto&current_weather=true"
            )

            response = requests.get(url, timeout=6)
            response.raise_for_status()
            resp = response.json()

            daily = resp.get("daily", {})
            current = resp.get("current_weather")
            hourly = resp.get("hourly", {})

            forecast = []
            for i in range(3):
                day_label = (
                    "Today" if i == 0 else (now + timedelta(days=i)).strftime("%a")
                )

                try:
                    daily_code = daily.get("weathercode", [None] * 3)[i]
                except IndexError:
                    daily_code = None

                try:
                    daily_temp = daily.get("temperature_2m_max", [None] * 3)[i]
                except IndexError:
                    daily_temp = None

                try:
                    daily_wind = daily.get("windspeed_10m_max", [None] * 3)[i]
                except IndexError:
                    daily_wind = None

                if i == 0 and current:
                    code = current.get("weathercode", daily_code)
                    temp = current.get("temperature", daily_temp or 0)
                    wind = current.get("windspeed", daily_wind or 0)
                else:
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

            cls._cache = forecast
            cls._last_update = now
            return cls._cache

        except Exception as e:
            current_app.logger.error(f"Weather fetch error: {str(e)}")
            return cls._cache or []
