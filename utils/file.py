__all__ = [
    "load_lines"
]


def load_lines(path: str, comment: str = "#", encoding: str = "utf-8-sig") -> list[str]:
    """
    Load non-empty, non-comment lines from a text file.

    Args:
        path: Path to the file
        comment: Prefix character for comment lines
        encoding: Text encoding (default utf-8-sig, strips BOM)

    Returns:
        List of stripped lines.
    """
    result = []
    with open(path, "r", encoding=encoding, errors="replace") as f:
        for ln in f:
            s = ln.strip()
            if s and not s.startswith(comment):
                result.append(s)
    return result
