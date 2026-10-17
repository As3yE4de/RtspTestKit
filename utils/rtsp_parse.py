from __future__ import annotations
import re

__all__ = [
    "parse_transport",
    "is_setup",
    "is_describe_response_with_sdp",
    "extract_sdp"
]


def parse_transport(payload: bytes) -> tuple[str | None, int | None, int | None]:
    """
    Take RTSP packet and parse Transport header to
    determine which protocol is used for RTP data.

    Args:
        payload: RTSP packet in byte

    Returns:
        ("udp", rtp_port, rtcp_port) for client_port
        ("tcp", ch1, ch2) for interleaved
        (None, None, None) when parsing failed
    """
    m = re.search(rb"client_port=(\d+)-(\d+)", payload)
    if m:
        return ("udp", int(m.group(1)), int(m.group(2)))
    m = re.search(rb"interleaved=(\d+)-(\d+)", payload)
    if m:
        return ("tcp", int(m.group(1)), int(m.group(2)))
    return (None, None, None)


def is_setup(payload: bytes) -> bool:
    """
    Check if the received RTSP packet using SETUP method.

    Args:
        payload: RTSP packet in byte

    Returns:
        True if it is RTSP SETUP; otherwise, returns False.
    """
    return payload.startswith(b"SETUP ")


def is_describe_response_with_sdp(payload: bytes) -> bool:
    """
    Check if the response to DESCRIBE request containing SDP data.

    Args:
        payload: RTSP packet in byte

    Returns:
        True if there is SDP data in response; otherwise, returns False.
    """
    return payload.startswith(b"RTSP/1.0 200") and b"application/sdp" in payload


def extract_sdp(payload: bytes) -> str | None:
    """
    Extract SDP information from RTSP DESCRIBE response.

    Args:
        payload: RTSP DESCRIBE response in byte

    Returns:
        SDP data.
    """
    idx = payload.find(b"\r\n\r\n")
    if idx == -1:
        return None
    try:
        sdp = payload[idx + 4:].decode("utf-8", errors="ignore")
    except Exception:
        return None
    if "m=video" in sdp or "m=audio" in sdp:
        return sdp
    return None
