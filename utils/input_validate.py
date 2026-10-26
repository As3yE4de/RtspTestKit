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
