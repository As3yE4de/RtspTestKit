__all__ = [
    "parse_status_line",
    "get_header",
    "get_headers"
]


def parse_status_line(data: bytes) -> tuple[int | None, str]:
    """
    Parse response to get the status code and the reason phrase.

    Args:
        data: Response in bytes

    Returns:
        (status_code, reason_phrase)
        - Success: (200, "OK")
        - Failed: (None, "")
    """
    if not data:
        return None, ""

    first = data.split(b"\r\n", 1)[0].decode("utf-8", errors="replace")

    parts = first.split(" ", 2)
    if len(parts) != 3:
        return None, ""

    if not parts[0].startswith("HTTP/"):
        return None, ""

    try:
        code = int(parts[1])
    except ValueError:
        return None, ""

    reason = parts[2] if len(parts) > 2 else ""
    return code, reason


def get_header(data: bytes, name: str) -> str | None:
    """
    Get the value of a specific header from a response.

    Args:
        data: Response in bytes
        name: Header name (case-insensitive)

    Returns:
        Value of the header, or none if the header not found.
    """
    if not data or not name:
        return None

    head = data.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")

    for line in head.split("\r\n")[1:]:
        if not line.strip():
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip().lower() == name.lower():
            return v.strip()
    return None


def get_headers(data: bytes) -> dict[str, list[str]]:
    """
    Parse all headers, preserve all values of headers with the same name.

    Args:
        data: Response or request in bytes

    Returns:
        Key-value pairs in dict.
    """
    if not data:
        return {}

    head = data.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")

    headers: dict[str, list[str]] = {}
    for line in head.split("\r\n")[1:]:
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip().lower()
        headers.setdefault(key, []).append(v.strip())
    return headers
