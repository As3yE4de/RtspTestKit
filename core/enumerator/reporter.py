from __future__ import annotations

from collections import defaultdict
from utils import tui as u
from core.enumerator import config as conf


class Stats:
    def __init__(self) -> None:
        """
        Initializer
        """
        self.total: int = 0
        self.err: int = 0
        self.found: int = 0
        self.by_status: defaultdict[str, int] = defaultdict(int)

    def update(self, result: dict, found_codes: frozenset[int] = conf.FOUND_STATUSES) -> None:
        """
        Update counters from a single probe result.

        Args:
            result: Dict produced by the worker, containing at least:
                    {"status": int | None, ...}
            found_codes: Set of status codes counted as "found".
        """
        self.total += 1

        status = result.get("status")
        if status is None:
            self.err += 1
            self.by_status["None"] += 1
        else:
            self.by_status[str(status)] += 1
            if status in found_codes:
                self.found += 1

    def reset(self) -> None:
        """
        Reset all counters to zero.
        """
        self.total = 0
        self.err = 0
        self.found = 0
        self.by_status.clear()

    def summary(self) -> str:
        """
        Return a formatted summary string (no colors, plain text).

        The caller is responsible for applying any styling.
        """
        lines = [
            f"Total  : {self.total}",
            f"Found  : {self.found}",
            f"Errors : {self.err}",
        ]

        if self.by_status:
            lines.append("By status:")
            for code, count in sorted(
                self.by_status.items(),
                key=lambda kv: (kv[0] == "None", int(kv[0]) if kv[0] != "None" else 0),
            ):
                lines.append(f"|__{code:<6}: {count}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"Stats(total={self.total}, found={self.found}, "
            f"err={self.err}, statuses={dict(self.by_status)})"
        )


def _classify(status: int | None) -> tuple[str, str, str]:
    """
    Classify the status code

    Args:
        status: The status code

    Returns:
        A tuple of:
            - Symbol
            - Color
            - Label
    """
    if status is None:
        return "[FAILED]", u.Retro.NEON_RED, "Connection failed"
    if status == 200:
        return "[SUCCESS]", u.Retro.NEON_GREEN, "OK"
    if status == 401:
        return "[WARNING]", u.Retro.NEON_YELLOW, "Unauthorized"
    if status == 403:
        return "[WARNING]", u.Retro.NEON_YELLOW, "Forbidden"
    if status == 404:
        return "[INFO]", u.Retro.NEON_BLUE, "Not Found"
    if status == 454:
        return "[INFO]", u.Retro.NEON_BLUE, "Session Not Found"
    return "[INFO]", u.Retro.NEON_BLUE, "Unknown"


def print_result(result: dict, verbose: bool) -> None:
    """
    Print a single probe result to stdout.

    Args:
        result: Dict produced by the worker:
                {"method", "path", "status", "reason", "recv_ms", "error"}
        verbose: If True, also print error details when present.
    """
    status = result["status"]
    symbol, color, label = _classify(status)

    method_col = f"{result['method']:<9}"
    symbol_col = f"{symbol:<15}"
    path_col   = f"{result['path']:<75}"
    status_col = f"{str(status) if status is not None else '---':<6}"
    time_col   = f"{result['recv_ms']:>8.1f}ms"

    line = (
        f"{u.colorize(method_col, u.Retro.CYAN)} "
        f"{u.colorize(path_col, color)} "
        f"{u.colorize(symbol_col, color + u.Retro.BOLD)} "
        f"{u.colorize(status_col, color)} "
        f"{u.colorize(time_col, u.Retro.CYAN)} "
        f"{u.colorize(label, color)}"
    )
    print(line)

    if verbose and result.get("error"):
        print(f"          {u.colorize('Error: ' + result['error'], u.Retro.NEON_RED + u.Retro.BOLD)}")


def write_result(out_fh, result: dict) -> None:
    """
    Write a result to a TSV file.

    Args:
        out_fh: File handle opened for writing
        result: Dict produced by the worker
    """
    if out_fh is None:
        return

    status = result["status"]
    line = (
        f"{result['method']}\t"
        f"{result['path']}\t"
        f"{status if status is not None else ''}\t"
        f"{result['recv_ms']:.1f}ms\t"
        f"{result['reason']}\t"
        f"{result.get('error') or ''}\n"
    )
    out_fh.write(line)
