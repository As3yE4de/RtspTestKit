from __future__ import annotations

from core.relay.config import MAX_INTERLEAVED_BUFFER, KEEP_TAIL


class InterleavedParser:
    def __init__(self) -> None:
        """
        Initializer
        """
        self.buf = bytearray()

    def reset(self) -> None:
        """
        Clean up parser's buffer
        """
        self.buf.clear()

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        """
        Take a TCP packet as data in byte to extract RTP interleaved frames.

        Args:
            data: TCP packet in byte.

        Returns:
            A list of tuples. Each tuple(channel, RTP data) in the returned list
            corresponds to a fully parsed interleaved frame.
        """
        frames = []
        self.buf.extend(data)

        while True:
            if len(self.buf) < 4:
                break
            if self.buf[0] != 0x24:
                idx = self.buf.find(b"$")
                if idx == -1:
                    if len(self.buf) > MAX_INTERLEAVED_BUFFER:
                        del self.buf[:-KEEP_TAIL]
                    break
                del self.buf[:idx]
                continue

            channel = self.buf[1]
            length = (self.buf[2] << 8) | self.buf[3]
            if len(self.buf) < 4 + length:
                break

            payload = bytes(self.buf[4:4 + length])
            frames.append((channel, payload))
            del self.buf[:4 + length]

        return frames
