"""Weather proxy — Open-Meteo API."""
import json
import logging
import urllib.request
import urllib.parse
from fastapi import APIRouter, Query, HTTPException
from config import OPEN_METEO_BASE

log = logging.getLogger("gitstat.weather")
weather_router = APIRouter(prefix="/api/weather", tags=["weather"])

# Chinese city coordinate lookup
_CITY_LOOKUP = [
    (34.34, 108.94, "西安"), (39.90, 116.40, "北京"), (31.23, 121.47, "上海"),
    (23.13, 113.26, "广州"), (22.54, 114.06, "深圳"), (30.57, 104.07, "成都"),
    (30.25, 120.17, "杭州"), (29.56, 106.55, "重庆"), (32.06, 118.79, "南京"),
    (36.07, 120.38, "青岛"), (28.23, 112.94, "长沙"), (30.59, 114.31, "武汉"),
    (25.04, 102.72, "昆明"), (29.65, 91.13, "拉萨"), (43.82, 87.62, "乌鲁木齐"),
    (45.80, 126.53, "哈尔滨"), (41.80, 123.43, "沈阳"),
]


def _resolve_city(lat: float, lon: float) -> str:
    best, best_dist = "", float("inf")
    for clat, clon, cname in _CITY_LOOKUP:
        dist = (lat - clat) ** 2 + (lon - clon) ** 2
        if dist < best_dist:
            best_dist, best = dist, cname
    return best if best_dist < 1.5 else ""


WMO_WEATHER_CODE = {
    0: {"zh": "晴", "en": "Clear", "icon": "clear"},
    1: {"zh": "大部晴朗", "en": "Mainly clear", "icon": "mostly-clear"},
    2: {"zh": "多云", "en": "Partly cloudy", "icon": "partly-cloudy"},
    3: {"zh": "阴", "en": "Overcast", "icon": "overcast"},
    45: {"zh": "雾", "en": "Fog", "icon": "fog"},
    48: {"zh": "冻雾", "en": "Depositing rime fog", "icon": "fog"},
    61: {"zh": "小雨", "en": "Slight rain", "icon": "rain"},
    63: {"zh": "中雨", "en": "Moderate rain", "icon": "rain"},
    65: {"zh": "大雨", "en": "Heavy rain", "icon": "rain"},
    71: {"zh": "小雪", "en": "Slight snow fall", "icon": "snow"},
    73: {"zh": "中雪", "en": "Moderate snow fall", "icon": "snow"},
    75: {"zh": "大雪", "en": "Heavy snow fall", "icon": "snow"},
    95: {"zh": "雷暴", "en": "Thunderstorm", "icon": "thunderstorm"},
}


def _fetch_open_meteo(params: dict) -> dict:
    url = OPEN_METEO_BASE + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitStat/2.2"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("Open-Meteo API error: %s", e)
        return {}


def _weather_desc(code: int, lang: str = "zh") -> str:
    info = WMO_WEATHER_CODE.get(code, {"zh": "未知", "en": "Unknown", "icon": "unknown"})
    return info.get(lang, info["en"])


def _weather_icon(code: int) -> str:
    return WMO_WEATHER_CODE.get(code, {"icon": "unknown"})["icon"]


@weather_router.get("/current")
def api_weather_current(lat: float = Query(...), lon: float = Query(...)):
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
    tz_name = _resolve_city(lat, lon) or tz.replace("Asia/", "").replace("Europe/", "").replace("America/", "") if tz else ""
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


@weather_router.get("/forecast")
def api_weather_forecast(lat: float = Query(...), lon: float = Query(...), days: int = Query(default=7)):
    data = _fetch_open_meteo({
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": min(max(days, 1), 7),
    })
    if not data or "daily" not in data:
        raise HTTPException(503, "Weather API unavailable")
    daily = data["daily"]
    forecast = []
    for i in range(len(daily.get("time", []))):
        code = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0
        forecast.append({
            "date": daily["time"][i],
            "weatherCode": code,
            "temperatureMax": daily.get("temperature_2m_max", [None])[i],
            "temperatureMin": daily.get("temperature_2m_min", [None])[i],
            "precipitation": daily.get("precipitation_sum", [0])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "windSpeedMax": daily.get("wind_speed_10m_max", [None])[i],
            "descriptionZh": _weather_desc(code, "zh"),
            "descriptionEn": _weather_desc(code, "en"),
            "icon": _weather_icon(code),
        })
    return {"code": 200, "data": forecast}
