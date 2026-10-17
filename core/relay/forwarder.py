from __future__ import annotations
import queue
import socket
import threading
import time

from core.relay.config import (
    PACKET_QUEUE_SIZE, RAW_SOCK_SNDBUF, VIEWER_HOST, LOG_INTERVAL,
)
from core.relay.packet_builder import build_ip_udp, init_raw_socket
from utils.tui import Retro


class ForwardStats:
    def __init__(self) -> None:
        """
        Initializer
        """
        self.lock = threading.Lock()
        self.rtp = 0
        self.rtcp = 0
        self.forwarded = 0
        self.dropped = 0
        self.filtered = 0

    def incr(self, key: str, n: int = 1) -> None:
        """
        Increase specific counter.

        Args:
            key: Name of counter
            n: Increase the counter by n
        """
        with self.lock:
            if not hasattr(self, key):
                setattr(self, key, 0)
            setattr(self, key, getattr(self, key) + n)

    def snapshot(self) -> dict[str, int]:
        """
        Create a snapshot of all counters.

        Returns:
            A dictionary of counter names and their values.
        """
        with self.lock:
            return {
                "rtp": self.rtp,
                "rtcp": self.rtcp,
                "forwarded": self.forwarded,
                "dropped": self.dropped,
                "filtered": self.filtered,
            }


class Forwarder:
    def __init__(self, viewer_port: int) -> None:
        """
        Initializer
        """
        self.viewer_port = viewer_port
        self.queue: queue.Queue = queue.Queue(maxsize=PACKET_QUEUE_SIZE)
        self.stats = ForwardStats()
        self.stop_flag = threading.Event()
        self._raw_sock = None
        self._thread = None
        self._last_log = 0.0
        self._log_lines = []

    def open_socket(self) -> None:
        """
        Open a new raw socket for sending packets.
        """
        self._raw_sock = init_raw_socket(RAW_SOCK_SNDBUF)

    def close_socket(self) -> None:
        """
        Close the existing raw socket if it is open.
        """
        if self._raw_sock:
            try:
                self._raw_sock.close()
            finally:
                self._raw_sock = None

    def enqueue(self, payload: bytes, dst_port: int) -> bool:
        """
        Send an RTP/RTCP packet along with its destination port to the queue.

        Args:
            payload: RTP packet in bytes.
            dst_port: Destination port.

        Returns:
            True if enqueued successfully; otherwise, returns False.
        """
        try:
            self.queue.put_nowait((payload, dst_port))
            return True
        except queue.Full:
            self.stats.incr("dropped")
            return False

    def start(self) -> None:
        """
        Start the background forwarding thread.
        """
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the forwarding thread gracefully and clean up the queue.
        """
        self.stop_flag.set()
        try:
            while True:
                self.queue.get_nowait()
        except queue.Empty:
            pass
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        """
        Main loop for the forwarding thread.
        
        Continuously pulls packets from the queue, builds the IP/UDP headers, 
        and sends them to the viewer. Also handles periodic logging.
        """
        self._last_log = time.time()
        while not self.stop_flag.is_set():
            try:
                item = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                break

            if self._raw_sock is None:
                self.stats.incr("dropped")
                continue

            payload, dst_port = item
            try:
                pkt = build_ip_udp(
                    VIEWER_HOST, VIEWER_HOST, 0, dst_port, payload
                )
                self._raw_sock.sendto(pkt, (VIEWER_HOST, dst_port))
                self.stats.incr("forwarded")
            except Exception as e:
                self.stats.incr("dropped")
                if self.stats.dropped <= 5:
                    print(f"{Retro.DEEP_PURP}[{Retro.NEON_RED}FAILED{Retro.DEEP_PURP}]{Retro.NEON_RED} {type(e).__name__}: {e}", flush=True)

            now = time.time()
            if now - self._last_log > LOG_INTERVAL:
                snap = self.stats.snapshot()
                print(
                    f"{Retro.DEEP_PURP}[{Retro.NEON_BLUE}INFO{Retro.DEEP_PURP}]{Retro.CYAN} "
                    f"Fwd={snap['forwarded']} RTP={snap['rtp']} RTCP={snap['rtcp']} "
                    f"Filtered={snap['filtered']} Drop={snap['dropped']} "
                    f"Q={self.queue.qsize()}{Retro.RESET}"
                )

                self._log_lines.append(
                    f"{Retro.DEEP_PURP}[{Retro.NEON_BLUE}INFO{Retro.DEEP_PURP}]{Retro.CYAN} "
                    f"Fwd={snap['forwarded']} RTP={snap['rtp']} RTCP={snap['rtcp']} "
                    f"Filtered={snap['filtered']} Drop={snap['dropped']} "
                    f"Q={self.queue.qsize()}{Retro.RESET}"
                )
                self._last_log = now

    def drain_logs(self) -> list[str]:
        """
        Retrieve and clear the accumulated log lines.

        Returns:
            A list of log lines.
        """
        lines, self._log_lines = self._log_lines, []
        return lines
