from __future__ import annotations
import subprocess
import threading
import time

from core.relay.config import SDP_PATH
from core.relay.sdp import rewrite_sdp_for_ffplay, default_h264_sdp
from utils import tui as u

class FfplayManager:
    def __init__(self, viewer_port: int) -> None:
        """
        Initializer
        """
        self.viewer_port = viewer_port
        self.proc = None
        self.lock = threading.Lock()
        self._events = []
        self._starting = False

    def _spawn(self, sdp: str) -> subprocess.Popen:
        """
        Spawn a subprocess for ffplay program using given SDP information.

        Args:
            sdp: SDP information

        Returns:
            An asynchronous fflay process.
        """
        with open(SDP_PATH, "w") as f:
            f.write(sdp)
        return subprocess.Popen([
            "ffplay",
            "-protocol_whitelist", "file,rtp,udp",
            "-i", SDP_PATH,
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-sync", "ext",
            "-probesize", "5000000",
            "-analyzeduration", "5000000",
        ])

    def start(self, real_sdp: str | None) -> int:
        """
        Start or restart ffplay.

        Args:
            real_sdp: Real SDP data captured from the RTSP server

        Returns:
            ffplay's PID.
        """
        with self.lock:
            if self._starting:
                return -1
            self._starting = True

        try:
            with self.lock:
                if self.proc and self.proc.poll() is None:
                    try:
                        self.proc.terminate()
                        self.proc.wait(timeout=2)
                    except Exception:
                        try:
                            self.proc.kill()
                        except Exception:
                            pass

            if real_sdp:
                sdp = rewrite_sdp_for_ffplay(real_sdp, self.viewer_port)
                self._events.append(
                    f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_GREEN}SUCCESS{u.Retro.DEEP_PURP}]{u.Retro.NEON_GREEN} Using captured SDP (port -> {self.viewer_port}){u.Retro.RESET}"
                )
            else:
                sdp = default_h264_sdp(self.viewer_port)
                self._events.append(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_YELLOW}WARNING{u.Retro.DEEP_PURP}]{u.Retro.CYAN} No SDP, using default H.264{u.Retro.RESET}")

            self.proc = self._spawn(sdp)
            self._events.append(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_GREEN}SUCCESS{u.Retro.DEEP_PURP}]{u.Retro.NEON_GREEN} ffplay started (PID {self.proc.pid}){u.Retro.RESET}")
            return self.proc.pid
        finally:
            with self.lock:
                self._starting = False

    def wait_and_launch(self, get_transport_mode: Callable[[], str | None],
                        get_real_sdp: Callable[[], str | None],
                        timeout_s: float = 60.0) -> int | None:
        """
        Wait for the maximum timeout until transport_mode + SDP received and then start.

        Args:
            get_transport_mode: Callable returning "tcp", "udp" or None
            get_real_sdp: Callable returning real SDP string or None
            timeout_s: Maximum waiting time for receiving SDP information from RTSP server

        Returns:
            ffplay's PID or None.
        """
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            mode = get_transport_mode()
            sdp = get_real_sdp()
            if mode and sdp:
                return self.start(sdp)
            time.sleep(0.5)

        if get_transport_mode():
            self._events.append(
                f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_YELLOW}WARNING{u.Retro.DEEP_PURP}]"
                f"{u.Retro.CYAN} SDP timeout, launching ffplay with default{u.Retro.RESET}"
            )
            return self.start(None)

        self._events.append(
            f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}]"
            f"{u.Retro.NEON_RED} No SETUP captured after timeout{u.Retro.RESET}"
        )
        return None

    def terminate(self) -> None:
        """
        Terminate ffplay process.
        """
        with self.lock:
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.terminate()
                except Exception:
                    self.proc.kill()

    def drain_events(self) -> list[str]:
        """
        Receive and clean up event logs.
        """
        events, self._events = self._events, []
        return events

