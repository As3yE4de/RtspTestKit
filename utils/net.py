import socket
import ssl

__all__ = [
    "recv_until_headers",
    "make_ssl_context"
]


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
