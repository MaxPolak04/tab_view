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

        # Cache TTL: 30 minutes (1800 seconds)
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

            # SRE Guardrail: Explicit 5s timeout avoids worker thread lockup
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            daily = data.get("daily", {})
            hourly = data.get("hourly", {})

            # --- 1. LEFT PANEL: Strictly [Now, +3h, +6h] ---
            today_forecast = []
            hourly_times = hourly.get("time", [])
            hourly_temps = hourly.get("temperature_2m", [])
            hourly_codes = hourly.get("weathercode", [])
            hourly_winds = hourly.get("windspeed_10m", [])

            if hourly_times:
                now_iso = now.replace(minute=0, second=0, microsecond=0).isoformat()
                current_idx = cls._nearest_hour_index(hourly_times, now_iso)

                for offset in [0, 3, 6]:
                    target_idx = current_idx + offset
                    if target_idx < len(hourly_times):
                        dt_hour = datetime.fromisoformat(hourly_times[target_idx])

                        if offset == 0:
                            time_label = "Teraz"
                        else:
                            time_label = dt_hour.strftime("%H:%M")

                        temp_val = (
                            hourly_temps[target_idx]
                            if target_idx < len(hourly_temps)
                            else None
                        )
                        wind_val = (
                            hourly_winds[target_idx]
                            if target_idx < len(hourly_winds)
                            else None
                        )
                        code_val = (
                            hourly_codes[target_idx]
                            if target_idx < len(hourly_codes)
                            else None
                        )

                        today_forecast.append(
                            {
                                "time": time_label,
                                "temp": round(float(temp_val))
                                if temp_val is not None
                                else "--",
                                "wind": round(float(wind_val))
                                if wind_val is not None
                                else "--",  # <--- DODANY WIATR DO SŁOWNIKA
                                "icon": cls._map_icon(code_val),
                            }
                        )

            # --- 2. RIGHT PANEL: Strictly 3 future days (Jutro, Pojutrze, Day +3) ---
            future_forecast = []
            daily_times = daily.get("time", [])
            daily_codes = daily.get("weathercode", [])
            daily_temps = daily.get("temperature_2m_max", [])
            daily_winds = daily.get("windspeed_10m_max", [])

            dni_pl = ["Pon", "Wto", "Śro", "Czw", "Pią", "Sob", "Nied"]

            # Range (1, 4) strictly grabs index 1, 2, and 3
            for i in range(1, min(len(daily_times), 4)):
                date_str = daily_times[i]
                dt_day = datetime.fromisoformat(date_str)

                if i == 1:
                    day_label = "Jutro"
                elif i == 2:
                    day_label = "Pojutrze"
                else:
                    day_label = dni_pl[dt_day.weekday()]

                temp_val = daily_temps[i] if i < len(daily_temps) else None
                wind_val = daily_winds[i] if i < len(daily_winds) else None
                code_val = daily_codes[i] if i < len(daily_codes) else None

                future_forecast.append(
                    {
                        "day": day_label,
                        "temp": round(float(temp_val))
                        if temp_val is not None
                        else "--",
                        "wind": round(float(wind_val))
                        if wind_val is not None
                        else "--",
                        "icon": cls._map_icon(code_val),
                    }
                )

            cls._cache = {"today": today_forecast, "future": future_forecast}
            cls._last_update = now
            return cls._cache

        except Exception as e:
            current_app.logger.error(f"Weather fetch error: {str(e)}")

            safe_fallback = {
                "today": [
                    {
                        "time": "Teraz",
                        "temp": "--",
                        "wind": "--",
                        "icon": "bi-cloud-slash",
                    },
                    {
                        "time": "+3h",
                        "temp": "--",
                        "wind": "--",
                        "icon": "bi-cloud-slash",
                    },
                    {
                        "time": "+6h",
                        "temp": "--",
                        "wind": "--",
                        "icon": "bi-cloud-slash",
                    },
                ],
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
                    {
                        "day": "Za 3 dni",
                        "temp": "--",
                        "wind": "--",
                        "icon": "bi-cloud-slash",
                    },
                ],
            }
            return cls._cache or safe_fallback
