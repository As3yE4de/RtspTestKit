import os
import re
import sys
import time

__all__ = [
    "Retro",
    "colorize",
    "print_banner",
    "print_retro_divider"
]


COLOR_ENABLED = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
ANSI_RE = re.compile(r"\033\[[0-9;]*m")

class Retro:
    RESET       = "\033[0m"
    BOLD        = "\033[1m"
    HOT_PINK    = "\033[38;5;205m"
    MAGENTA     = "\033[38;5;201m"
    PURPLE      = "\033[38;5;135m"
    DEEP_PURP   = "\033[38;5;93m"
    CYAN        = "\033[38;5;51m"
    TEAL        = "\033[38;5;45m"
    SUNSET_ORG  = "\033[38;5;208m"
    SUNSET_YEL  = "\033[38;5;220m"
    NEON_BLUE   = "\033[38;5;27m"
    NEON_RED    = "\033[38;5;196m"
    NEON_GREEN  = "\033[38;5;46m"
    NEON_YELLOW = "\033[38;5;226m"
    GRID_PINK   = "\033[38;5;198m"
    GRADIENT  = [
        "\033[38;5;219m", "\033[38;5;213m", "\033[38;5;177m",
        "\033[38;5;141m", "\033[38;5;105m", "\033[38;5;69m",
    ]

Retro.INFO = f"{Retro.HOT_PINK}[{Retro.NEON_BLUE}INFO{Retro.HOT_PINK}]{Retro.CYAN} "
Retro.SUCCESS = f"{Retro.HOT_PINK}[{Retro.NEON_GREEN}SUCCESS{Retro.HOT_PINK}]{Retro.NEON_GREEN} "
Retro.FAILED = f"{Retro.HOT_PINK}[{Retro.NEON_RED}FAILED{Retro.HOT_PINK}]{Retro.NEON_RED} "
Retro.WARNING = f"{Retro.HOT_PINK}[{Retro.NEON_YELLOW}WARNING{Retro.HOT_PINK}]{Retro.NEON_YELLOW} "

def _visible_len(text: str) -> int:
    """
    Get the visible length of a string, ignoring ANSI escape codes.

    Args:
        text: A text string possibly containing ANSI escape codes

    Returns:
        The number of visible characters.
    """
    return len(ANSI_RE.sub("", text))


def colorize(text: str, color: str) -> str:
    """
    Cover a text string with color.

    Args:
        text: A text string need to be colorized
        color: Color name from Retro class

    Returns:
        A colorized text string.
    """
    if not COLOR_ENABLED:
        return text
    return f"{color}{text}{Retro.RESET}"


def _load_banner(file_path: str) -> list[str] | None:
    """
    Load banner from a specific text file.

    Args:
        file_path: Path to the banner file

    Returns:
        A list of lines in banner file.
    """
    if not os.path.isfile(file_path):
        print(f"{Retro.DEEP_PURP}[{Retro.NEON_RED}FAILED{Retro.DEEP_PURP}]{Retro.NEON_RED} Banner not found: {file_path}{Retro.RESET}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().rstrip("\n").splitlines()
    except Exception as e:
        print(f"{Retro.DEEP_PURP}[{Retro.NEON_RED}FAILED{Retro.DEEP_PURP}]{Retro.NEON_RED} Error reading banner: {e}{Retro.RESET}")
        return None


def print_banner(file_path: str, glow: bool = True, typing: bool = False, delay: float = 0.002, subtitle: str = "") -> None:
    """
    Print banner with Retrowave/Synthwave style in 90s.

    Args:
        file_path : Path to banner file (.txt)
        glow      : Turn on gradient Miami sunset
        typing    : Character-by-character typing effect
        delay     : Delay between characters while typing
        subtitle  : Subtitle below the banner (optional)
    """
    lines = _load_banner(file_path)
    if not lines:
        return

    total = len(lines)
    width = max(len(l) for l in lines)
    grad = Retro.GRADIENT

    if typing:
        for i, line in enumerate(lines):
            color = grad[int(i / max(total - 1, 1) * (len(grad) - 1))] if glow else Retro.CYAN
            if COLOR_ENABLED:
                sys.stdout.write(color)
            for ch in line:
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(delay if ch != " " else delay * 0.3)
            if COLOR_ENABLED:
                sys.stdout.write(Retro.RESET)
            print()
    else:
        for i, line in enumerate(lines):
            color = grad[int(i / max(total - 1, 1) * (len(grad) - 1))] if glow else Retro.CYAN
            if COLOR_ENABLED:
                print(f"{color}{line}{Retro.RESET}")
            else:
                print(line)

    if subtitle:
        for sub_line in subtitle.splitlines():
            print(sub_line)

    _gradient_line(width)
    print()


def _gradient_line(width: int, char: str = "═") -> None:
    """
    Print a gradient line.

    Args:
        width: The length of the line
        char: Print a line with a specific character
    """
    if not COLOR_ENABLED:
        print(char * width)
        return

    grad = Retro.GRADIENT
    out = []
    for x in range(width):
        color = grad[int(x / max(width - 1, 1) * (len(grad) - 1))]
        out.append(f"{color}{char}")
    out.append(Retro.RESET)
    print("".join(out))


def print_retro_divider(width: int = 60) -> None:
    """
    Gradient divider for use between sections.

    Args:
        width: The length of the divider
    """
    _gradient_line(width, "─")
