from __future__ import annotations
import socket
import ssl
import time

from core.enumerator import build_probe as bp
from core.enumerator import config as cf
from utils.rtsp_parse import parse_status_line
from utils.auth import build_basic_auth, build_digest_auth, find_auth_scheme, parse_digest_challenge
from utils.net import recv_until_headers, make_ssl_context


def probe(host: str, port: int, path: str, timeout: float = 5.0, method: str = "DESCRIBE", use_tls: bool = False,
          username: str | None = None, password: str | None = None) -> tuple[int | None, str, float, str | None]:
    """
    Check whether a specific RTSP path is existing without authentication.

    Args:
        host: IP/domain server
        port: RTSP/RTSPS port
        path: RTSP path
        timeout: Maximum waiting time for responses
        method: RTSP method
        use_tls: True if using RTSP over TLS
        username: Username for authentication
        password: Password for authentication

    Returns:
        A tuple of:
            - status
            - reason
            - recv_ms
            - error
    """
    scheme = "rtsps" if use_tls else "rtsp"
    url = f"{scheme}://{host}:{port}{path}"

    if username is not None and password is not None:
        return _auth_probe(method, host, port, path, username, password, timeout, use_tls)

    req = bp.build_probe(method, url)

    sock = None
    recv_ms = 0.0
    try:
        raw_sock = socket.create_connection((host, port), timeout=timeout)
        if use_tls:
            ctx = make_ssl_context()
            try:
                sock = ctx.wrap_socket(raw_sock, server_hostname=host)
            except ssl.SSLError:
                raw_sock.close()
                return None, "", 0.0, "TLS handshake failed"
        else:
            sock = raw_sock

        sock.sendall(req)

        t0 = time.perf_counter()
        data = recv_until_headers(sock, cf.READ_BYTES * 2)
        recv_ms = (time.perf_counter() - t0) * 1000

        status, reason = parse_status_line(data)
        return status, reason, recv_ms, None

    except socket.timeout:
        return None, "", recv_ms, "timeout"
    except ConnectionRefusedError:
        return None, "", recv_ms, "connection refused"
    except ssl.SSLError as e:
        return None, "", recv_ms, f"TLS error: {e}"
    except OSError as e:
        return None, "", recv_ms, str(e)
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass

def _auth_probe(method: str, host: str, port: int, path: str, username: str, password: str,
               timeout: float = 5.0, use_tls: bool = False) -> tuple[int | None, str, float, str | None]:
    """
    Probe an RTSP URL using credentials.
    - Send an unauthenticated request first.
    - If 401 + Digest -> parse the challenge and resend using Digest.
    - If 401 + Basic  -> resend using Basic credentials.

    Args:
        method: RTSP method
        host: IP/domain server
        port: RTSP/RTSPS port
        path: RTSP path
        username: Username for authentication
        password: Password for authentication
        timeout: Maximum waiting time for responses
        use_tls: True if using RTSP over TLS

    Returns:
        A tuple of:
            - status
            - reason
            - recv_ms
            - error
    """
    scheme = "rtsps" if use_tls else "rtsp"
    url = f"{scheme}://{host}:{port}{path}"

    sock = None
    recv_ms = 0.0

    try:
        raw_sock = socket.create_connection((host, port), timeout=timeout)
        if use_tls:
            ctx = make_ssl_context()
            try:
                sock = ctx.wrap_socket(raw_sock, server_hostname=host)
            except ssl.SSLError:
                raw_sock.close()
                return None, "", 0.0, "TLS handshake failed"
        else:
            sock = raw_sock

        cseq = 1
        for attempt in range(cf.MAX_ATTEMPTS):
            req = bp.build_probe(method, url, cseq=cseq)
            cseq += 1
            sock.sendall(req)

            t0 = time.perf_counter()
            data = recv_until_headers(sock)
            recv_ms = (time.perf_counter() - t0) * 1000

            status, reason = parse_status_line(data)
            if status != 401:
                return status, reason, recv_ms, None

            auth_scheme, raw_value = find_auth_scheme(data)
            if auth_scheme is None:
                return status, reason, recv_ms, "401 without supported WWW-Authenticate"

            if auth_scheme == "basic":
                auth_header = build_basic_auth(username, password)
                req = bp.build_probe(method, url, cseq=cseq, auth_header=auth_header)
                cseq += 1
                sock.sendall(req)

                t0 = time.perf_counter()
                data = recv_until_headers(sock)
                recv_ms = (time.perf_counter() - t0) * 1000

                status, reason = parse_status_line(data)
                if status != 401:
                    return status, reason, recv_ms, None
                return status, reason, recv_ms, "Invalid HTTP Basic authentication"

            params = parse_digest_challenge(raw_value)
            digest_header = build_digest_auth(
                username, password, method, url, params, nc=attempt + 1
            )
            req = bp.build_probe(method, url, cseq=cseq, auth_header=digest_header)
            cseq += 1
            sock.sendall(req)

            t0 = time.perf_counter()
            data = recv_until_headers(sock)
            recv_ms = (time.perf_counter() - t0) * 1000

            status, reason = parse_status_line(data)
            if status != 401:
                return status, reason, recv_ms, None

            next_scheme, next_value = find_auth_scheme(data)
            if next_scheme == "digest" and next_value and "stale=true" in next_value.lower():
                continue

            return status, reason, recv_ms, "Invalid HTTP Digest authentication"

        return status, reason, recv_ms, "auth retry exhausted"

    except socket.timeout:
        return None, "", recv_ms, "timeout"
    except ConnectionRefusedError:
        return None, "", recv_ms, "connection refused"
    except ssl.SSLError as e:
        return None, "", recv_ms, f"TLS error: {e}"
    except OSError as e:
        return None, "", recv_ms, str(e)
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass
