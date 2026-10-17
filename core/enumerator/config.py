from pathlib import Path

from version import __version__, __author__
from utils.tui import Retro

# --- About ---
AUTHOR = __author__
VERSION = __version__
GITHUB = "https://github.com/As3yE4de"
SUBTITLE = (
    f"{Retro.DEEP_PURP}[{Retro.NEON_BLUE}INFO{Retro.DEEP_PURP}] "
    f"{Retro.CYAN}Author  : {Retro.HOT_PINK}{AUTHOR}{Retro.RESET}\n"
    f"{Retro.DEEP_PURP}[{Retro.NEON_BLUE}INFO{Retro.DEEP_PURP}] "
    f"{Retro.CYAN}Version : {Retro.HOT_PINK}{VERSION}{Retro.RESET}\n"
    f"{Retro.DEEP_PURP}[{Retro.NEON_BLUE}INFO{Retro.DEEP_PURP}] "
    f"{Retro.CYAN}Github  : {Retro.HOT_PINK}{GITHUB}{Retro.RESET}"
)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_BANNER = BASE_DIR / "assets" / "banner.txt"

# --- Default Settings ---
DEFAULT_TIMEOUT = 4.0
DEFAULT_THREADS = 20
DEFAULT_DELAY = 0.0
MAX_ATTEMPTS = 3
READ_BYTES = 4096
DEFAULT_USER_AGENT = "Lavf62.12.102"
DEFAULT_RTSP_PORT = 554
DEFAULT_RTSPS_PORT = 322

# RTSP status codes considered "path exists" (may require auth)
FOUND_STATUSES = frozenset({200, 401, 403, 454, 455})
