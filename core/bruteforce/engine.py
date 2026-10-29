from __future__ import annotations
import socket
import ssl

from core.bruteforce import config as cf
from utils.auth import (
    build_basic_auth,
    build_digest_auth,
    find_auth_scheme,
    parse_digest_challenge,
)
from utils.rtsp_parse import parse_status_line
from utils.net import make_ssl_context, recv_until_headers


__all__ = ["try_credentials"]


def _split_url(url: str) -> tuple[str, int, str, bool]:
    """
    Split an RTSP/RTSPS URL into (host, port, path, use_tls).

    Args:
        url: Full URL like 'rtsp://host:554/path' or 'rtsps://host:322/path'.

    Returns:
        A tuple of (host, port, path, use_tls).
    """
    use_tls = url.lower().startswith("rtsps://")
    scheme = "rtsps" if use_tls else "rtsp"
    rest = url[len(scheme) + 3:]

    if "/" in rest:
        authority, path = rest.split("/", 1)
        path = "/" + path
    else:
        authority, path = rest, "/"

    if ":" in authority:
        host, port_s = authority.rsplit(":", 1)
        port = int(port_s)
    else:
        host = authority
        port = 322 if use_tls else 554

    return host, port, path, use_tls


def _build_request(method: str, uri: str, cseq: int,
                   auth_header: str | None = None) -> bytes:
    """
    Build a minimal RTSP request.

    Args:
        method: RTSP method (e.g. DESCRIBE).
        uri: Request URI (full RTSP URL).
        cseq: RTSP CSeq header value.
        auth_header: Optional Authorization header value.

    Returns:
        Encoded request bytes.
    """
    lines = [
        f"{method} {uri} RTSP/1.0",
        f"CSeq: {cseq}",
        f"User-Agent: {cf.DEFAULT_USER_AGENT}",
    ]
    if auth_header:
        lines.append(f"Authorization: {auth_header}")
    lines += ["", ""]
    return "\r\n".join(lines).encode()


def _open_socket(host: str, port: int, use_tls: bool,
                 timeout: float) -> socket.socket:
    """
    Open a TCP (or TLS) connection to host:port.

    Args:
        host: Server hostname or IP.
        port: Server port.
        use_tls: True to wrap the socket with TLS.
        timeout: Connection timeout in seconds.

    Returns:
        A connected socket object.
    """
    raw = socket.create_connection((host, port), timeout=timeout)
    if not use_tls:
        return raw
    ctx = make_ssl_context()
    return ctx.wrap_socket(raw, server_hostname=host)


def _classify_status(status: int | None, reason: str) -> tuple[bool, str]:
    """
    Map an RTSP status code to (ok, message) for brute-force purposes.

    Only 2xx is considered success. 401 is a credential failure. Any other
    status is a non-credential failure (e.g. wrong path, forbidden).

    Args:
        status: RTSP status code, or None on transport error.
        reason: RTSP reason phrase.

    Returns:
        A tuple of (ok, message).
    """
    if status is None:
        return False, "no status"

    if 200 <= status < 300:
        return True, f"{status} {reason}".strip()

    if status == 401:
        return False, "unauthorized"

    return False, f"{status} {reason}".strip()


def try_credentials(url: str, method: str, username: str, password: str,
                    timeout: float, use_tls: bool) -> tuple[bool, str]:
    """
    Try one (username, password) pair against an RTSP server.

    Sends an unauthenticated request first to obtain the challenge, then
    resends with Basic or Digest authorization. Handles stale nonce retries.

    A credential is considered valid only if the server responds with a 2xx
    status after authentication. 401 means the credential is wrong. Any other
    status (403, 404, 5xx, ...) is reported as a non-credential failure so
    the caller can distinguish wrong password from wrong path / forbidden.

    Args:
        url: Full RTSP/RTSPS URL (from create_url).
        method: RTSP method used for authentication (e.g. DESCRIBE).
        username: Username to try.
        password: Password to try.
        timeout: Maximum wait time for responses, in seconds.
        use_tls: True to use RTSP over TLS (rtsps://).

    Returns:
        A tuple of (ok, message):
        - ok: True if the server accepted the credential (2xx response).
        - message: Human-readable status or error description.
    """
    host, port, _path, _ = _split_url(url)

    try:
        sock = _open_socket(host, port, use_tls, timeout)
    except socket.timeout:
        return False, "timeout"
    except ConnectionRefusedError:
        return False, "connection refused"
    except ssl.SSLError as e:
        return False, f"TLS error: {e}"
    except OSError as e:
        return False, str(e)

    try:
        cseq = 1
        last_status: int | None = None
        last_reason: str = ""

        for attempt in range(cf.MAX_ATTEMPTS):
            sock.sendall(_build_request(method, url, cseq=cseq))
            cseq += 1

            try:
                data = recv_until_headers(sock, cf.READ_BYTES * 2)
            except socket.timeout:
                return False, "timeout"

            status, reason = parse_status_line(data)
            last_status, last_reason = status, reason

            if status is not None and 200 <= status < 300:
                return True, f"{status} {reason}".strip()
            if status != 401:
                return _classify_status(status, reason)

            scheme, raw_value = find_auth_scheme(data)
            if scheme is None:
                return False, f"{status} {reason}".strip()

            if scheme == "basic":
                auth_header = build_basic_auth(username, password)
            else:
                params = parse_digest_challenge(raw_value)
                auth_header = build_digest_auth(
                    username, password, method, url, params,
                    nc=attempt + 1,
                )

            sock.sendall(_build_request(method, url, cseq=cseq,
                                        auth_header=auth_header))
            cseq += 1

            try:
                data = recv_until_headers(sock, cf.READ_BYTES * 2)
            except socket.timeout:
                return False, "timeout"

            status, reason = parse_status_line(data)
            last_status, last_reason = status, reason

            if status is not None and 200 <= status < 300:
                return True, f"{status} {reason}".strip()

            if status == 401:
                next_scheme, next_value = find_auth_scheme(data)
                if (next_scheme == "digest" and next_value
                        and "stale=true" in next_value.lower()):
                    continue
                return False, f"{status} {reason}".strip()

            return _classify_status(status, reason)

        return False, f"auth retry exhausted ({last_status} {last_reason})".strip()

    except socket.timeout:
        return False, "timeout"
    except ConnectionRefusedError:
        return False, "connection refused"
    except ssl.SSLError as e:
        return False, f"TLS error: {e}"
    except OSError as e:
        return False, str(e)
    finally:
        try:
            sock.close()
        except OSError:
            pass
