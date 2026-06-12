"""Weather proxy — wttr.in (国内可访问) + Open-Meteo fallback."""
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

# wttr.in weather code → WMO code mapping
_WTTR_CODE_MAP = {
    113: 0,   # Clear/Sunny
    116: 2,   # Partly cloudy
    119: 3,   # Cloudy
    122: 3,   # Overcast
    143: 45,  # Mist
    176: 61,  # Patchy rain
    179: 71,  # Patchy snow
    182: 61,  # Patchy sleet
    200: 95,  # Thunderstorm
    227: 73,  # Blowing snow
    230: 75,  # Blizzard
    248: 45,  # Fog
    260: 45,  # Freezing fog
    263: 61,  # Patchy light drizzle
    266: 61,  # Light drizzle
    281: 61,  # Freezing drizzle
    284: 61,  # Heavy freezing drizzle
    293: 61,  # Patchy light rain
    296: 61,  # Light rain
    299: 63,  # Moderate rain
    302: 65,  # Heavy rain
    305: 65,  # Heavy rain
    308: 65,  # Very heavy rain
    311: 61,  # Light freezing rain
    314: 65,  # Moderate freezing rain
    317: 61,  # Light sleet
    320: 63,  # Moderate sleet
    323: 71,  # Patchy light snow
    326: 71,  # Light snow
    329: 73,  # Moderate snow
    332: 73,  # Moderate snow
    335: 75,  # Heavy snow
    338: 75,  # Very heavy snow
    350: 61,  # Ice pellets
    353: 61,  # Patchy light rain
    356: 65,  # Moderate rain
    359: 65,  # Heavy rain
    362: 61,  # Light sleet
    365: 63,  # Moderate sleet
    368: 71,  # Light snow
    371: 73,  # Moderate snow
    374: 61,  # Light ice pellets
    377: 65,  # Heavy ice pellets
    386: 95,  # Patchy thunderstorm
    389: 95,  # Thunderstorm
    392: 95,  # Patchy thunderstorm with snow
    395: 95,  # Thunderstorm with snow
}


def _weather_desc(code: int, lang: str = "zh") -> str:
    info = WMO_WEATHER_CODE.get(code, {"zh": "未知", "en": "Unknown", "icon": "unknown"})
    return info.get(lang, info["en"])


def _weather_icon(code: int) -> str:
    return WMO_WEATHER_CODE.get(code, {"icon": "unknown"})["icon"]


def _fetch_wttr(city: str) -> dict:
    """Fetch weather from wttr.in (国内可访问)."""
    encoded_city = urllib.parse.quote(city)
    url = f"https://wttr.in/{encoded_city}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitStat/2.2"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("wttr.in API error: %s", e)
        return {}


def _fetch_open_meteo(params: dict) -> dict:
    """Fetch weather from Open-Meteo (海外可用)."""
    url = OPEN_METEO_BASE + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitStat/2.2"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("Open-Meteo API error: %s", e)
        return {}


def _wttr_to_wmo(wttr_code: int) -> int:
    """Convert wttr.in weather code to WMO code."""
    return _WTTR_CODE_MAP.get(wttr_code, 0)


@weather_router.get("/current")
def api_weather_current(lat: float = Query(...), lon: float = Query(...)):
    city = _resolve_city(lat, lon)

    # 优先尝试 wttr.in（国内可用）
    wttr_data = _fetch_wttr(city) if city else {}
    if wttr_data and "current_condition" in wttr_data:
        cur = wttr_data["current_condition"][0]
        wttr_code = int(cur.get("weatherCode", 113))
        wmo_code = _wttr_to_wmo(wttr_code)
        feels_like = float(cur.get("FeelsLikeC", cur.get("temp_C", 0)))
        return {
            "code": 200,
            "data": {
                "temperature": float(cur.get("temp_C", 0)),
                "apparentTemperature": feels_like,
                "humidity": float(cur.get("humidity", 0)),
                "windSpeed": float(cur.get("windspeedKmph", 0)),
                "weatherCode": wmo_code,
                "descriptionZh": _weather_desc(wmo_code, "zh"),
                "descriptionEn": _weather_desc(wmo_code, "en"),
                "icon": _weather_icon(wmo_code),
                "timezone": wttr_data.get("nearest_area", [{}])[0].get("region", [city])[0] if wttr_data.get("nearest_area") else "",
                "locationName": city,
                "units": {"temperature_2m": "°C", "relative_humidity_2m": "%", "wind_speed_10m": "km/h"},
            },
        }

    # 备用：Open-Meteo
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
    tz_name = city or (tz.replace("Asia/", "").replace("Europe/", "").replace("America/", "") if tz else "")
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
    city = _resolve_city(lat, lon)

    # 优先尝试 wttr.in
    wttr_data = _fetch_wttr(city) if city else {}
    if wttr_data and "weather" in wttr_data:
        forecast = []
        for day_data in wttr_data.get("weather", []):
            wttr_code = int(day_data.get("hourly", [{}])[0].get("weatherCode", 113)) if day_data.get("hourly") else 113
            # 取日均WMO码
            hourly_codes = [int(h.get("weatherCode", 113)) for h in day_data.get("hourly", [])]
            avg_code = max(set(hourly_codes), key=hourly_codes.count) if hourly_codes else 113
            wmo_code = _wttr_to_wmo(avg_code)
            forecast.append({
                "date": day_data.get("date", ""),
                "weatherCode": wmo_code,
                "temperatureMax": float(day_data.get("maxtempC", 0)),
                "temperatureMin": float(day_data.get("mintempC", 0)),
                "precipitation": float(day_data.get("hourly", [{}])[4].get("precipMM", 0)) if len(day_data.get("hourly", [])) > 4 else 0,
                "windSpeedMax": float(day_data.get("hourly", [{}])[4].get("windspeedKmph", 0)) if len(day_data.get("hourly", [])) > 4 else 0,
                "descriptionZh": _weather_desc(wmo_code, "zh"),
                "descriptionEn": _weather_desc(wmo_code, "en"),
                "icon": _weather_icon(wmo_code),
            })
        return {"code": 200, "data": forecast[:min(max(days, 1), 7)]}

    # 备用：Open-Meteo
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