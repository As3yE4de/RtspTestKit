from __future__ import annotations

from core.relay.config import MIN_RTP_HEADER


def is_valid_rtp(packet: bytes, payload_types: set[int] | None = None) -> bool:
    """
    Check if the input packet is actually RTP packet.

    Args:
        packet: Data in byte.

    Returns:
        True if the data is RTP packet; otherwise, returns False.
    """
    if len(packet) < MIN_RTP_HEADER:
        return False
    if ((packet[0] >> 6) & 0x03) != 2:
        return False
    if payload_types is None:
        return True
    return (packet[1] & 0x7F) in payload_types


class SsrcLock:
    def __init__(self) -> None:
        """
        Initializer
        """
        self._locks: dict[str, int] = {}

    def reset(self) -> None:
        """
        Clear all locked SSRCs.
        """
        self._locks.clear()

    def accept(self, packet: bytes, is_audio: bool = False) -> tuple[bool, int | None]:
        """
        Check if the packet's SSRC is valid or lock it if it's the first time seeing it.

        Args:
            packet: RTP packet in bytes.
            is_audio: True if the packet belongs to the audio track, False for video.

        Returns:
            A tuple of (accepted, new_locked_ssrc).
            - accepted: True if the packet is accepted, False if it's filtered.
            - new_locked_ssrc: The newly locked SSRC integer, or None if already locked.
        """
        if len(packet) < MIN_RTP_HEADER:
            return False, None
        ssrc = int.from_bytes(packet[8:12], "big")
        key = "audio" if is_audio else "video"

        locked = self._locks.get(key)
        if locked is None:
            self._locks[key] = ssrc
            return True, ssrc
        if ssrc == locked:
            return True, None
        return False, None
