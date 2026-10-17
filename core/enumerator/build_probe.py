from __future__ import annotations
import secrets


def build_probe(method: str, url: str, cseq: int = 1, user_agent: str = "Lavf62.12.102", session: str | None = None,
                  placeholder_session: str | None = None,
                  auth_header: str | None = None) -> bytes:
    """
    Build a RTSP request for probing.

    Args:
        method: RTSP method (DESCRIBE, OPTIONS, SETUP, PLAY, GET_PARAMETER, ANNOUNCE, RECORD)
        url: Full RTSP URL (schemas can be rtsp:// or rtsps://)
        cseq: Request sequence number
        user_agent: An user-agent string for the request
        session: Real Session ID
        placeholder_session: Random session ID for testing
        auth_header: Authorization header for authentication

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

    if auth_header:
        lines.append(f"Authorization: {auth_header}")

    request = "\r\n".join(lines) + "\r\n\r\n"
    if body:
        request += body

    return request.encode("utf-8", errors="replace")
