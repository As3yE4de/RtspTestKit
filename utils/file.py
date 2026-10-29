__all__ = [
    "load_stripped_lines",
    "load_password_lines"
]


def load_stripped_lines(path: str, comment: str = "#", encoding: str = "utf-8-sig") -> list[str]:
    """
    Load lines from a text file.

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

def load_password_lines(path: str, comment: str = "#", encoding: str = "utf-8-sig") -> list[str]:
    """
    Load password lines from a text file.

    Unlike normal line loading, passwords may contain leading/trailing spaces,
    so we only strip the trailing newline (and optional BOM) while preserving
    all other whitespace exactly as written.

    Args:
        path: Path to the file
        comment: Prefix character for comment lines (checked after stripping
                 surrounding whitespace, so "   # foo" is treated as a comment)
        encoding: Text encoding (default utf-8-sig, strips BOM)

    Returns:
        List of password lines with newlines removed but spaces preserved.
    """
    result = []
    with open(path, "r", encoding=encoding, errors="replace") as f:
        for ln in f:
            line = ln.rstrip("\r\n")
            if not line:
                continue
            stripped = line.strip()
            if not stripped or stripped.startswith(comment):
                continue
            result.append(line)
    return result
