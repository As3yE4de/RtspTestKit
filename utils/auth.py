import base64
import hashlib
import os
import re

from utils.http_parse import get_headers

__all__ = [
    "build_basic_auth",
    "build_digest_auth",
    "parse_digest_challenge",
    "find_auth_scheme"
]


def build_basic_auth(user: str, password: str) -> str:
    """
    Create the value of Authorization header for HTTP Basic Authentication.

    Args:
        user: Username for authentication
        password: Password for authentication

    Returns:
        A base64-encoded string for HTTP Basic authentication.
    """
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def build_digest_auth(user: str, password: str, method: str, uri: str,
                challenge: dict, nc: int = 1) -> str:
    """
    Create Authorization header using HTTP Digest authentication.

    Args:
        user: Username for authentication
        password: Password for authentication
        method: HTTP/RTSP method
        uri: Request URI
        challenge: A dictionary contains params of WWW-Authenticate header
        nc: Nonce count, increasing on each retry with the same nonce

    Returns:
        A hashed string for HTTP Digest authentication.
    """
    realm = challenge.get("realm", "")
    nonce = challenge.get("nonce", "")
    qop = challenge.get("qop")
    opaque = challenge.get("opaque")
    algorithm = challenge.get("algorithm", "MD5").upper()

    if algorithm == "MD5":
        H = hashlib.md5
    elif algorithm == "SHA-256":
        H = hashlib.sha256
    else:
        H = hashlib.md5

    def hash_hex(s: str) -> str:
        return H(s.encode("utf-8")).hexdigest()

    ha1 = hash_hex(f"{user}:{realm}:{password}")
    ha2 = hash_hex(f"{method}:{uri}")

    if qop:
        qop_options = [q.strip() for q in qop.split(",")]
        qop_val = "auth" if "auth" in qop_options else qop_options[0]
        nc_val = f"{nc:08x}"
        cnonce = os.urandom(8).hex()
        response = hash_hex(f"{ha1}:{nonce}:{nc_val}:{cnonce}:{qop_val}:{ha2}")
    else:
        nc_val = None
        cnonce = None
        qop_val = None
        response = hash_hex(f"{ha1}:{nonce}:{ha2}")

    parts = [
        f'username="{user}"',
        f'realm="{realm}"',
        f'nonce="{nonce}"',
        f'uri="{uri}"',
        f'response="{response}"',
    ]

    if "algorithm" in challenge:
        parts.append(f"algorithm={algorithm}")

    if opaque:
        parts.append(f'opaque="{opaque}"')
    if qop_val:
        parts.append(f"qop={qop_val}")
        parts.append(f"nc={nc_val}")
        parts.append(f'cnonce="{cnonce}"')

    return "Digest " + ", ".join(parts)


def parse_digest_challenge(header_value: str) -> dict:
    """
    Parse the value of WWW-Authenticate header to get all parameters.

    Args:
        header_value: The value of WWW-Authenticate header in string

    Returns:
        A dictionary of WWW-Authenticate header's parameters.
    """
    params = {}

    body = header_value.strip()
    if body.lower().startswith("digest"):
        body = body[len("digest"):].strip()

    for match in re.finditer(r'(\w+)\s*=\s*(?:"([^"]*)"|([^,\s]+))', body):
        key = match.group(1).lower()
        val = match.group(2) if match.group(2) is not None else match.group(3)
        params[key] = val
    return params


def find_auth_scheme(data: bytes) -> tuple[str | None, str | None]:
    """
    Find the first supported auth scheme and its raw challenge value
    from a raw HTTP/RTSP response.

    Priority: Digest > Basic.

    Args:
        data: Response in bytes

    Returns:
        A tuple of (scheme, raw_value) where scheme is "digest", "basic",
        or None if no supported scheme is found.
    """
    headers = get_headers(data)
    values = headers.get("www-authenticate", [])

    for value in values:
        if value.strip().lower().startswith("digest"):
            return "digest", value

    for value in values:
        if value.strip().lower().startswith("basic"):
            return "basic", value

    return None, None
