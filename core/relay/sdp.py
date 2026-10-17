from __future__ import annotations

# Port convention:
#   viewer_port      -> RTP video
#   viewer_port + 1  -> RTCP video
#   viewer_port + 2  -> RTP audio
#   viewer_port + 3  -> RTCP audio

def parse_media_payload_types(sdp: str) -> set[int]:
    """
    Parse SDP and extract all RTP payload types from both video and audio m= lines.

    Args:
        sdp: SDP data in string format.

    Returns:
        A set of payload type integers.
    """
    types: set[int] = set()
    for line in sdp.splitlines():
        if not (line.startswith("m=video") or line.startswith("m=audio")):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        for pt in parts[3:]:
            try:
                types.add(int(pt))
            except ValueError:
                continue
    return types

def parse_audio_payload_types(sdp: str) -> set[int]:
    """
    Parse SDP and extract RTP payload types specifically from audio m= lines.

    Args:
        sdp: SDP data in string format.

    Returns:
        A set of payload type integers for audio streams.
    """
    types: set[int] = set()
    for line in sdp.splitlines():
        if not line.startswith("m=audio"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        for pt in parts[3:]:
            try:
                types.add(int(pt))
            except ValueError:
                continue
    return types

def rewrite_sdp_for_ffplay(sdp: str, viewer_port: int) -> str:
    video_port = viewer_port
    audio_port = viewer_port + 2

    lines = sdp.replace("\r\n", "\n").split("\n")
    out = []
    has_conn = any(line.startswith("c=") for line in lines)

    for line in lines:
        if line.startswith("c="):
            out.append("c=IN IP4 127.0.0.1")
            continue

        if line.startswith("m=video"):
            parts = line.split()
            if len(parts) >= 2:
                parts[1] = str(video_port)
            out.append(" ".join(parts))
            continue

        if line.startswith("m=audio"):
            parts = line.split()
            if len(parts) >= 2:
                parts[1] = str(audio_port)
            out.append(" ".join(parts))
            continue

        out.append(line)

    if not has_conn:
        for i, line in enumerate(out):
            if line.startswith("s="):
                out.insert(i + 1, "c=IN IP4 127.0.0.1")
                break

    return "\n".join(out) + "\n"


def default_h264_sdp(viewer_port: int) -> str:
    """
    Create a default SDP payload for H.264 video.

    This is used as a fallback when the tool fails to capture the real SDP 
    from the RTSP server within the timeout period.

    Args:
        viewer_port: The port where the local player (ffplay) will receive the stream.

    Returns:
        A default SDP data string.
    """
    return (
        f"v=0\no=- 0 0 IN IP4 127.0.0.1\ns=Tap\n"
        f"c=IN IP4 127.0.0.1\nt=0 0\n"
        f"m=video {viewer_port} RTP/AVP 96\n"
        f"a=rtpmap:96 H264/90000\na=fmtp:96 packetization-mode=1\n"
    )
