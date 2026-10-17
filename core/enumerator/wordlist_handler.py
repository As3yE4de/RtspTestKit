from __future__ import annotations
from urllib.parse import urlparse
from utils.file import load_lines


def load_url_pathlist(path: str) -> list[str]:
    """
    Load a list of URL paths.

    Args:
        path: Path to the wordlist

    Returns:
        Lines in the wordlist in list.
    """
    result = []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        for ln in f:
            s = ln.strip()
            if s and not s.startswith("#"):
                result.append(s)
    return result


def dedupe_url_paths(raw_paths: list[str]) -> list[str]:
    """
    Remove duplicated raw paths.

    Args:
        raw_paths: List of raw paths (can get from load_url_pathlist())

    Returns:
        List of normalize paths, no duplicated, keep order.
    """
    seen = set()
    result = []
    for p in raw_paths:
        np = _normalize_url_path(p)
        if np not in seen:
            seen.add(np)
            result.append(np)
    return result


def _normalize_url_path(p: str) -> str:
    """
    Standardize a URL path by stripping scheme/host and ensuring leading slash.

    Args:
        p: Raw URL path

    Returns:
        Standardized URL path.
    """
    p = p.strip()
    if not p:
        return "/"

    if p.lower().startswith(("rtsp://", "rtsps://", "http://", "https://")):
        parsed = urlparse(p)
        p = parsed.path or "/"

    if not p.startswith("/"):
        p = "/" + p

    while p.startswith("//"):
        p = p[1:]

    return p
