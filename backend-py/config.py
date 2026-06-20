"""Application configuration."""
from pathlib import Path
import os

VERSION = "2.2.0-py"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12580
MAX_COMMITS_PER_REPO = 5000
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
GITSTAT_HOME = Path(os.environ.get("GITSTAT_HOME", Path.home() / ".gitstat")).expanduser()
DEFAULT_SCAN_ROOT = str(Path.home())

# Skip noisy/system/cache dirs when recursively discovering repos under home.
SCAN_SKIP_DIR_NAMES = frozenset({
    "Library", "Applications", "node_modules", ".npm", ".cache",
    ".Trash", "Trash", ".codex", ".nvm", ".gitstat-gitee-cache",
    "venv", ".venv", "__pycache__", ".pytest_cache", "site-packages",
    "Pods", ".gradle", "DerivedData", "Cache", "Caches",
})


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
GITEE_CACHE_DIR = Path(os.environ.get("GITSTAT_GITEE_CACHE_DIR", Path.home() / ".gitstat-gitee-cache")).expanduser()
GITEE_ACCESS_TOKEN = os.environ.get("GITEE_TOKEN", "")

# Caching
GIT_LOG_CACHE_TTL = 300  # 5 minutes

# Weather
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
