import ipaddress
from ping3 import ping
import re
import socket
import ssl

__all__ = [
    "is_host_reachable",
    "classify_host_input",
    "recv_until_headers",
    "make_ssl_context"
]


_HOSTNAME_LABEL = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_IPV4_LIKE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_HAS_LETTER = re.compile(r"[A-Za-z]")


def _is_valid_hostname(host: str) -> bool:
    """
    Check if the supplied string is a valid hostname.

    Args:
        host: Input string

    Returns:
        True if the input is a valid hostname; otherwise, returns False.
    """
    if not host or len(host) > 253:
        return False

    name = host[:-1] if host.endswith(".") else host
    if not name:
        return False

    labels = name.split(".")

    if len(labels) < 2 and name.lower() != "localhost":
        return False

    if not _HAS_LETTER.search(labels[-1]):
        return False

    return all(_HOSTNAME_LABEL.match(lb) for lb in labels)

def _is_valid_netmask(packed: int) -> bool:
    """
    Check if the supplied string is a valid subnetmask.

    Args:
        host: Input string

    Returns:
        True if the input is a valid subnetmask; otherwise, returns False.
    """
    inverted = (~packed) & 0xFFFFFFFF
    return (inverted & (inverted + 1)) == 0

def classify_host_input(s: str) -> tuple[str, str | None]:
    """
    Classify the input string

    Returns:
        ("ipv4", None)        If the string is a valid IPv4 address (Ex: "192.168.1.1")
        ("netmask", None)     If the string is a valid netmask (Ex: "255.255.255.0")
        ("hostname", None)    If the string is a valid hostname (Ex: "example.com")
        ("invalid", "reason") If the string is invalid
    """
    if not isinstance(s, str):
        return "invalid", f"Data type is not string (str): {type(s).__name__}"

    s = s.strip()
    if not s:
        return "invalid", "empty string"

    try:
        packed = int(ipaddress.IPv4Address(s))
    except ValueError:
        packed = None

    if packed is not None:
        if _is_valid_netmask(packed):
            return "netmask", None
        return "ipv4", None

    if _IPV4_LIKE.match(s):
        return "invalid", f"'{s}' looks like an IPv4 address but is not valid"

    if _is_valid_hostname(s):
        return "hostname", None

    return "invalid", f"'{s}' is not a valid IPv4 address, hostname or netmask"

def is_host_reachable(host: str, timeout: float = 4.0, retries: int = 3) -> tuple[bool, str | None, float | None]:
    """
    Check if the server responds to ICMP pings.

    Args:
        host: IP/Domain name (Ex: "google.com", "8.8.8.8")
        timeout: Maximum waiting time per ping (seconds)
        retries: Maximum retries

    Returns:
        (True, None, rtt) if host responses to ICMP requests.
        (False, "reason", None) if host cannot be reachable or error.
    """
    if retries < 1:
        return False, f"retries must be >= 1 (received {retries})", None

    last_error: str | None = None

    for attempt in range(1, retries + 1):
        try:
            result = ping(host, timeout=timeout)
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            continue

        if result is None:
            last_error = f"timeout after {timeout}s"
            continue
        if result is False:
            last_error = f"cannot resolve or an error occurs while sending ICMP to '{host}'"
            continue

        return True, None, result

    return False, f"failed after {retries} retries, last erro: {last_error}", None

def recv_until_headers(sock: socket.socket, max_bytes: int = 8192,
                       read_bytes: int = 4096) -> bytes:
    """
    Read from socket until reaching '\\r\\n\\r\\n' (end of HTTP/RTSP headers),
    or reaching max_bytes, or reaching EOF.

    Args:
        sock: Socket receiving data
        max_bytes: Maximum limit for reading bytes
        read_bytes: Size of each recv() call

    Returns:
        Raw bytes have been read.
    """
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(read_bytes)
        if not chunk:
            break
        data += chunk
        if len(data) > max_bytes:
            break
    return data


def make_ssl_context(insecure: bool = True,
                     min_version: ssl.TLSVersion | None = ssl.TLSVersion.TLSv1) -> ssl.SSLContext:
    """
    Create a SSL/TLS context.

    Args:
        insecure: If True, disable hostname check and certificate verification.
        min_version: Minimum TLS version, or None to use system default.

    Returns:
        An ssl.SSLContext object.
    """
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    if min_version is not None:
        try:
            ctx.minimum_version = min_version
        except (AttributeError, ValueError):
            pass
    return ctx
