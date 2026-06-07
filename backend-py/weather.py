"""Weather proxy — Open-Meteo API."""
import json
import urllib.request
import urllib.parse
from fastapi import APIRouter, Query, HTTPException
from config import OPEN_METEO_BASE

weather_router = APIRouter(prefix="/api/weather", tags=["weather"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WMO_WEATHER_CODE = {
    0: {"zh": "晴", "en": "Clear", "icon": "clear"},
    1: {"zh": "大部晴朗", "en": "Mainly clear", "icon": "mostly-clear"},
    2: {"zh": "多云", "en": "Partly cloudy", "icon": "partly-cloudy"},
    3: {"zh": "阴", "en": "Overcast", "icon": "overcast"},
    45: {"zh": "雾", "en": "Fog", "icon": "fog"},
    48: {"zh": "冻雾", "en": "Depositing rime fog", "icon": "fog"},
    51: {"zh": "小毛毛雨", "en": "Light drizzle", "icon": "drizzle"},
    53: {"zh": "毛毛雨", "en": "Moderate drizzle", "icon": "drizzle"},
    55: {"zh": "大毛毛雨", "en": "Dense drizzle", "icon": "drizzle"},
    56: {"zh": "冻毛毛雨", "en": "Light freezing drizzle", "icon": "drizzle"},
    57: {"zh": "冻毛毛雨", "en": "Dense freezing drizzle", "icon": "drizzle"},
    61: {"zh": "小雨", "en": "Slight rain", "icon": "rain"},
    63: {"zh": "中雨", "en": "Moderate rain", "icon": "rain"},
    65: {"zh": "大雨", "en": "Heavy rain", "icon": "rain"},
    66: {"zh": "冻雨", "en": "Light freezing rain", "icon": "rain"},
    67: {"zh": "冻雨", "en": "Heavy freezing rain", "icon": "rain"},
    71: {"zh": "小雪", "en": "Slight snow fall", "icon": "snow"},
    73: {"zh": "中雪", "en": "Moderate snow fall", "icon": "snow"},
    75: {"zh": "大雪", "en": "Heavy snow fall", "icon": "snow"},
    77: {"zh": "雪粒", "en": "Snow grains", "icon": "snow"},
    80: {"zh": "小阵雨", "en": "Slight rain showers", "icon": "rain"},
    81: {"zh": "中阵雨", "en": "Moderate rain showers", "icon": "rain"},
    82: {"zh": "大阵雨", "en": "Violent rain showers", "icon": "rain"},
    85: {"zh": "小阵雪", "en": "Slight snow showers", "icon": "snow"},
    86: {"zh": "大阵雪", "en": "Heavy snow showers", "icon": "snow"},
    95: {"zh": "雷暴", "en": "Thunderstorm", "icon": "thunderstorm"},
    96: {"zh": "雷暴+小冰雹", "en": "Thunderstorm with slight hail", "icon": "thunderstorm"},
    99: {"zh": "雷暴+大冰雹", "en": "Thunderstorm with heavy hail", "icon": "thunderstorm"},
}

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def _fetch_open_meteo(params: dict) -> dict:
    """调用 Open-Meteo API 并返回 JSON。"""
    url = OPEN_METEO_BASE + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitStat/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("Open-Meteo API error: %s", e)
        return {}


def _weather_desc(code: int, lang: str = "zh") -> str:
    info = WMO_WEATHER_CODE.get(code, {"zh": "未知", "en": "Unknown", "icon": "unknown"})
    return info.get(lang, info["en"])


def _weather_icon(code: int) -> str:
    info = WMO_WEATHER_CODE.get(code, {"icon": "unknown"})
    return info["icon"]


@weather_router.get("/api/weather/current")
def api_weather_current(lat: float = Query(...), lon: float = Query(...)):
    """获取当前天气（代理 Open-Meteo）。"""
    data = _fetch_open_meteo({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
        "timezone": "auto",
    })
    if not data or "current" not in data:
        raise HTTPException(503, "Weather API unavailable")

    cur = data["current"]
    tz = data.get("timezone", "")
    tz_name = tz.replace("Asia/", "").replace("Europe/", "").replace("America/", "") if tz else ""

    return {
        "code": 200,
        "data": {
            "temperature": cur.get("temperature_2m"),
            "apparentTemperature": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "windSpeed": cur.get("wind_speed_10m"),
            "weatherCode": cur.get("weather_code"),
            "descriptionZh": _weather_desc(cur.get("weather_code", 0), "zh"),
            "descriptionEn": _weather_desc(cur.get("weather_code", 0), "en"),
            "icon": _weather_icon(cur.get("weather_code", 0)),
            "timezone": tz,
            "locationName": tz_name,
            "units": data.get("current_units", {}),
        },
    }


@weather_router.get("/api/weather/forecast")
def api_weather_forecast(lat: float = Query(...), lon: float = Query(...), days: int = Query(default=7)):
    """获取未来几天天气预报（代理 Open-Meteo）。"""
    data = _fetch_open_meteo({
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": min(days, 7),
    })
    if not data or "daily" not in data:
        raise HTTPException(503, "Weather API unavailable")

    daily = data["daily"]
    forecast = []
    for i in range(len(daily.get("time", []))):
        entry = {
            "date": daily["time"][i],
            "weatherCode": daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0,
            "temperatureMax": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "temperatureMin": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "apparentTemperatureMax": daily.get("apparent_temperature_max", [])[i] if i < len(daily.get("apparent_temperature_max", [])) else None,
            "apparentTemperatureMin": daily.get("apparent_temperature_min", [])[i] if i < len(daily.get("apparent_temperature_min", [])) else None,
            "sunrise": daily.get("sunrise", [])[i] if i < len(daily.get("sunrise", [])) else "",
            "sunset": daily.get("sunset", [])[i] if i < len(daily.get("sunset", [])) else "",
            "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "windSpeedMax": daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
            "descriptionZh": _weather_desc(daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0, "zh"),
            "descriptionEn": _weather_desc(daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0, "en"),
            "icon": _weather_icon(daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0),
        }
        forecast.append(entry)

    return {
        "code": 200,
        "data": forecast,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

weather_router = APIRouter(prefix="/api/weather", tags=["weather"])
# Routes are decorated above; FastAPI picks them up via module import
