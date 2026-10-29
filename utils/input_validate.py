import ipaddress
import re

__all__ = [
    "parse_ports",
    "is_a_single_ipv4",
    "is_a_single_port",
    "is_a_single_hostname"
]


_HOSTNAME_LABEL = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_HAS_LETTER = re.compile(r"[A-Za-z]")


def parse_ports(port_input: str) -> list[int]:
    """
    Validate and resolve the input string into a list of integer ports.
    Support: single port, comma-separated list of ports and port range.

    Args:
        port_input: Input string

    Returns:
        List of ports.
    """
    port_input = port_input.strip().lower()
    ports = set()
    parts = port_input.split(',')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if '-' in part:
            sub_parts = part.split('-')
            if len(sub_parts) != 2:
                raise ValueError(f"Invalid format port range: '{part}'")

            start_str, end_str = sub_parts
            if not (start_str.isdigit() and end_str.isdigit()):
                raise ValueError(f"Port range must only contain integers: '{part}'")

            start, end = int(start_str), int(end_str)

            if not (1 <= start <= 65535 and 1 <= end <= 65535):
                raise ValueError(f"Port must be between from  1 to 65535: '{part}'")
            if start > end:
                raise ValueError(f"The start port of the range must not be greater than the end port of the range: '{part}'")

            ports.update(range(start, end + 1))
        else:
            if not part.isdigit():
                raise ValueError(f"Invalid port: '{part}'")
            port = int(part)
            if not (1 <= port <= 65535):
                raise ValueError(f"Port must be between from  1 to 65535: '{port}'")
            ports.add(port)
    return sorted(list(ports))

def is_a_single_ipv4(s: str) -> bool:
    """
    Check if the given string is a single valid IPv4 address.

    Args:
        s: Input string

    Returns:
        True if the string is a single valid IPv4 address; otherwise, returns False
    """
    if not isinstance(s, str):
        return False

    value = s.strip()
    if not value:
        return False

    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False

    return ip.version == 4

def is_a_single_port(s: str) -> bool:
    """
    Check if the given string is a single valid network port.

    Args:
        s: Input string

    Returns:
        True if the given string is a single valid port number; otherwise, returns False.
    """
    if not isinstance(s, str):
        return False

    value = s.strip()
    if not value:
        return False

    if not value.isdigit():
        return False

    port = int(value)
    return 1 <= port <= 65535

def is_a_single_hostname(s: str) -> bool:
    """
    Check if the supplied string is a single valid hostname.

    Args:
        host: Input string

    Returns:
        True if the input is a valid hostname; otherwise, returns False.
    """
    if not s or len(s) > 253:
        return False

    name = s[:-1] if s.endswith(".") else s
    if not name:
        return False

    labels = name.split(".")

    if len(labels) < 2 and name.lower() != "localhost":
        return False

    if not _HAS_LETTER.search(labels[-1]):
        return False

    return all(_HOSTNAME_LABEL.match(lb) for lb in labels)
