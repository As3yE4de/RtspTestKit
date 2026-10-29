from pathlib import Path

from version import __version__, __author__
from utils.tui import Retro

# --- About ---
AUTHOR = __author__
VERSION = __version__
GITHUB = "https://github.com/As3yE4de"
SUBTITLE = (
    f"{Retro.HOT_PINK}[{Retro.NEON_BLUE}INFO{Retro.HOT_PINK}] "
    f"{Retro.CYAN}Author  : {Retro.HOT_PINK}{AUTHOR}{Retro.RESET}\n"
    f"{Retro.HOT_PINK}[{Retro.NEON_BLUE}INFO{Retro.HOT_PINK}] "
    f"{Retro.CYAN}Version : {Retro.HOT_PINK}{VERSION}{Retro.RESET}\n"
    f"{Retro.HOT_PINK}[{Retro.NEON_BLUE}INFO{Retro.HOT_PINK}] "
    f"{Retro.CYAN}Github  : {Retro.HOT_PINK}{GITHUB}{Retro.RESET}"
)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_BANNER = BASE_DIR / "assets" / "banner.txt"

# --- Default Settings ---
DEFAULT_TIMEOUT = 4.0
DEFAULT_THREADS = 20
DEFAULT_DELAY = 0.0
COMMON_RTSP_PORTS = [554, 555, 5544, 5454, 8554, 10554, 5000]
