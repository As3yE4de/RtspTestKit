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
DEFAULT_RTSP_PORT = 554
DEFAULT_VIEWER_PORT = 50000
DEFAULT_IFACE = "eth0"
VIEWER_HOST = "127.0.0.1"
SDP_PATH = "/tmp/tap.sdp"
RAW_SOCK_SNDBUF = 4 * 1024 * 1024
PACKET_QUEUE_SIZE = 131072
MIN_RTP_HEADER = 12
RTP_PAYLOAD_TYPE = 96
LOG_INTERVAL = 2.0
MAX_INTERLEAVED_BUFFER = 65536
KEEP_TAIL = 4096
QUEUE_NUM = 200
