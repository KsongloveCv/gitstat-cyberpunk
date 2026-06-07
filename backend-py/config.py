"""Application configuration."""
from pathlib import Path
import os

VERSION = "2.1.0-py"
MAX_COMMITS_PER_REPO = 5000
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


class Timeout:
    """Centralized timeout constants (seconds)."""
    GIT_EXEC = 30
    GIT_CLONE = 120
    GIT_PULL = 60
    GIT_VERSION = 5
    GIT_LOG_PARSE = 30
    HTTP_API = 15
    WEATHER_API = 10
    QUICK = 5


# Gitee API
GITEE_API_BASE = "https://gitee.com/api/v5"
GITEE_CACHE_DIR = Path.home() / ".gitstat-gitee-cache"
GITEE_ACCESS_TOKEN = os.environ.get("GITEE_TOKEN", "")

# Caching
GIT_LOG_CACHE_TTL = 300  # 5 minutes

# Weather
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
