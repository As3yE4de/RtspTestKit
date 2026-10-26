from __future__ import annotations
import secrets
import socket
import concurrent.futures
from queue import Queue

from core.scan import config as cf
from utils.rtsp_parse import create_url
from utils.net import make_ssl_context

def _build_rtsp_request(method: str, url: str = "/", cseq: int = 1, user_agent: str = "Lavf62.12.102", session: str | None = None,
                        placeholder_session: str | None = None) -> bytes:
    """
    Build a RTSP request for probing.

    Args:
        method: RTSP method (DESCRIBE, OPTIONS, SETUP, PLAY, GET_PARAMETER, ANNOUNCE, RECORD)
        url: Full RTSP URL (schemas can be rtsp:// or rtsps://)
        cseq: Request sequence number
        user_agent: An user-agent string for the request
        session: Real Session ID
        placeholder_session: Random session ID for testing

    Returns:
        The complete RTSP request in bytes
    """
    if placeholder_session is None:
        placeholder_session = "".join(secrets.choice("0123456789") for _ in range(8))

    body = ""

    if method.upper() == "OPTIONS":
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "DESCRIBE":
        lines = [
            f"{method} {url} RTSP/1.0",
            "Accept: application/sdp",
            f"CSeq: {cseq}",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "SETUP":
        lines = [
            f"{method} {url} RTSP/1.0",
            "Transport: RTP/AVP/TCP;unicast;interleaved=0-1",
            f"CSeq: {cseq}",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "PLAY":
        lines = [
            f"{method} {url} RTSP/1.0",
            "Transport: RTP/AVP/TCP;unicast;interleaved=0-1",
            f"CSeq: {cseq}",
            f"Session: {session or placeholder_session}",
            "Range: npt=10-15",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "PAUSE":
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            f"Session: {session or placeholder_session}",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "RECORD":
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            f"Session: {session or placeholder_session}",
            "Conference: 128.16.64.19/32492374",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "TEARDOWN":
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            f"Session: {session or placeholder_session}",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "GET_PARAMETER":
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            "Content-Type: text/parameters",
            f"Session: {session or placeholder_session}",
            "Content-Length: 0",
            f"User-Agent: {user_agent}",
        ]
    elif method.upper() == "ANNOUNCE":
        body = "v=0\r\no=- 0 0 IN IP4 0.0.0.0\r\ns=probe\r\nt=0 0\r\n"
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            "Date: 23 Jan 1997 15:35:06 GMT",
            f"Session: {session or placeholder_session}",
            "Content-Type: application/sdp",
            f"Content-Length: {len(body)}",
            f"User-Agent: {user_agent}",
        ]
    else:
        lines = [
            f"{method} {url} RTSP/1.0",
            f"CSeq: {cseq}",
            f"User-Agent: {user_agent}",
        ]

    request = "\r\n".join(lines) + "\r\n\r\n"
    if body:
        request += body

    return request.encode("utf-8", errors="replace")

def _is_rtsps_port(host: str, port: int, method: str, timeout: float) -> bool:
    """
    Send RTSP request to confirm RTSP over TLS port.

    Args:
        host: IP/hostname of the target
        port: Target port
        method: RTSP method to use
        timeout: Maximum waiting time for each request

    Returns:
        True if the port is RTSPS port; otherwise, returns False
    """
    url = create_url(host, port, "/")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))

            req = _build_rtsp_request(method, url)
            ctx = make_ssl_context()

            try:
                sock = ctx.wrap_socket(s, server_hostname=host)
            except ssl.SSLError:
                sock.close()
                return False

            sock.sendall(req)
            response = sock.recv(1024).decode('utf-8', errors='ignore')

            if response.startswith("RTSP/"):
                return True
    except Exception as e:
        print(f"{e}")
        pass
    return False

def _is_rtsp_port(host: str, port: int, method: str, timeout: float) -> bool:
    """
    Send RTSP request to confirm RTSP port.

    Args:
        host: IP/hostname of the target
        port: Target port
        method: RTSP method to use
        timeout: Maximum waiting time for each request

    Returns:
        True if the port is RTSP port; otherwise, returns False
    """
    url = create_url(host, port, "/")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))

            req = _build_rtsp_request(method, url)

            s.sendall(req)
            response = s.recv(1024).decode('utf-8', errors='ignore')

            if response.startswith("RTSP/"):
                return True
    except Exception as e:
        print(f"{e}")
        pass
    return False

def _check_port(host: str, port: int, method: str, timeout: float, delay: float) -> tuple | None:
    """
    Check the open port by opening a full TCP connection.
    If open, continue checking if it is RTSP port.

    Args:
        host: IP/hostname of the target
        port: Port to be scanned
        method: RTSP method to use
        timeout: Maximum waiting time for each connections
        delay: Interval between RTSP request

    Returns:
        A tuple of (host, port, "open", "is RTPS port")
    """
    if delay > 0:
        time.sleep(delay)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) == 0:
                if _is_rtsp_port(host, port, method, timeout):
                    return (host, port, "open", "RTSP")
                elif _is_rtsps_port(host, port, method, timeout):
                    return (host, port, "open", "RTSPS")
                else:
                    return (host, port, "open", "Unknown")
    except Exception:
        pass

    return None

def start_scan(targets: list[str], ports: list[int], method: str, timeout: float, delay: float, n_threads: int) -> list[tuple]:
    """
    Scan ports on the targets in parallel.

    Args:
        targets: List of targets
        ports: List of ports need to be scanned
        method: RTSP method to use
        timeout: Maximum waiting time for each connections
        delay: Interval between RTSP request
        n_threads: Specified N thread(s) for the scanning process

    Returns:
        Returns a list of tuples including (host, port, state)
    """
    results = []
    tasks = []

    for ip in targets:
        for port in ports:
            tasks.append((ip, port))

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = []
        for ip, port in tasks:
            future = executor.submit(_check_port, ip, port, method, timeout, delay)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    return results
