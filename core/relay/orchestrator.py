from __future__ import annotations
import argparse
import os
import subprocess
import sys
import threading

from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, UDP

from core.relay.config import QUEUE_NUM
from core.relay.logger import Logger
from core.relay.interleaved import InterleavedParser
from core.relay.rtp import SsrcLock, is_valid_rtp
from utils.rtsp_parse import (
    is_setup,
    is_describe_response_with_sdp,
    parse_transport,
    extract_sdp,
)
from core.relay.forwarder import Forwarder
from core.relay.ffplay_manager import FfplayManager
from core.relay.iptables_manager import IptablesManager
from utils.tui import Retro
from core.relay.sdp import parse_media_payload_types, parse_audio_payload_types


class RtspTap:
    def __init__(self, args: argparse.Namespace) -> None:
        """
        Initializer
        """
        self.args = args
        self.logger = Logger(debug=args.debug)
        self.transport_mode: str | None = None
        self.rtp_ports: set[int] = set()
        self.rtcp_ports: set[int] = set()
        self.real_sdp: str | None = None
        self.payload_types: set[int] | None = None
        self.parser = InterleavedParser()
        self.ssrc = SsrcLock()
        self.forwarder = Forwarder(viewer_port=args.viewer_port)
        self.ffplay = FfplayManager(viewer_port=args.viewer_port)
        self.iptables = IptablesManager(
            iface=args.iface, rtsp_port=args.rtsp_port
        )
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()
        self._audio_pts: set[int] = set()

    def _reset_session(self) -> None:
        """
        Reset RTSP session state, clearing all parsers, locks, and cached data.
        """
        self.parser.reset()
        self.ssrc.reset()
        self.transport_mode = None
        self.real_sdp = None
        self.payload_types = None
        self._audio_pts.clear()
        self.rtp_ports.clear()
        self.rtcp_ports.clear()
        self.logger.log(
            f"{Retro.INFO}Session state reset{Retro.RESET}"
        )

    @staticmethod
    def _sysctl(key: str, val: str) -> None:
        """
        Execute sysctl command.

        Args:
            key: Key
            val: Value
        """
        subprocess.run(
            ["sysctl", "-w", f"{key}={val}"],
            check=False, capture_output=True,
        )

    def process_packet(self, pkt: netfilterqueue.packet.Packet) -> None:
        """
        Filtering and routing packets which go through kernel queue (NFQUEUE).

        Args:
            pkt: Packet object
        """
        data = pkt.get_payload()
        if len(data) < 20:
            pkt.accept()
            return

        try:
            sp = IP(data)
        except Exception:
            pkt.accept()
            return

        if sp.haslayer(UDP):
            self._handle_udp(pkt, sp)
            return

        if not sp.haslayer(TCP):
            pkt.accept()
            return

        self._handle_tcp(pkt, sp)

    def _handle_udp(self, pkt, sp) -> None:
        """
        Process UDP packets traversing the NFQUEUE.

        Args:
            pkt: The NFQUEUE packet object.
            sp: The Scapy IP packet object.
        """
        udp = sp[UDP]
        dport = udp.dport

        with self._lock:
            is_rtp = dport in self.rtp_ports
            is_rtcp = dport in self.rtcp_ports
            payload_types = self.payload_types
            audio_pts = self._audio_pts

        if is_rtp:
            payload = bytes(udp.payload)
            if is_valid_rtp(payload, payload_types):
                pt = payload[1] & 0x7F
                is_audio = pt in audio_pts
                accepted, new_ssrc = self.ssrc.accept(payload, is_audio)
                if accepted:
                    dst = self.args.viewer_port + 2 if is_audio else self.args.viewer_port
                    self.forwarder.enqueue(payload, dst)
                    self.forwarder.stats.incr("rtp")
                    if new_ssrc is not None:
                        self.logger.log(
                            f"{Retro.SUCCESS}Locked SSRC 0x{new_ssrc:08x} "
                            f"({'audio' if is_audio else 'video'}, PT={pt}){Retro.RESET}"
                        )
                else:
                    self.forwarder.stats.incr("filtered")

        elif is_rtcp:
            payload = bytes(udp.payload)
            self.forwarder.enqueue(payload, self.args.viewer_port + 1)
            self.forwarder.stats.incr("rtcp")

        pkt.accept()

    def _handle_tcp(self, pkt, sp) -> None:
        """
        Process TCP packets (RTSP commands and interleaved data) traversing the NFQUEUE.

        Args:
            pkt: The NFQUEUE packet object.
            sp: The Scapy IP packet object.
        """
        tcp = sp[TCP]
        if tcp.dport != self.args.rtsp_port and tcp.sport != self.args.rtsp_port:
            pkt.accept()
            return

        payload = bytes(tcp.payload) if tcp.payload else b""

        if is_setup(payload):
            mode, p1, p2 = parse_transport(payload)
            if mode:
                with self._lock:
                    if self.transport_mode is not None and self.transport_mode != mode:
                        self._reset_session()
                    self.transport_mode = mode
                    if mode == "udp":
                        self.rtp_ports.add(p1)
                        self.rtcp_ports.add(p2)
                self.logger.log(
                    f"{Retro.SUCCESS}SETUP: mode={mode}, p1={p1}, p2={p2}{Retro.RESET}"
                )
                if mode == "udp":
                    self.iptables.install_udp_rule(p1)
                    self.iptables.install_udp_rule(p2)

        if is_describe_response_with_sdp(payload):
            sdp = extract_sdp(payload)
            if sdp:
                with self._lock:
                    sdp_changed = (
                        self.real_sdp is not None and self.real_sdp != sdp
                    )
                    self.real_sdp = sdp
                    self.payload_types = parse_media_payload_types(sdp) or None
                    self._audio_pts = parse_audio_payload_types(sdp)
                self.logger.log(
                    f"{Retro.SUCCESS}SDP captured "
                    f"({len(sdp)} bytes, payload types: {sorted(self.payload_types or [])})"
                    f"{Retro.RESET}"
                )

        with self._lock:
            mode = self.transport_mode
            payload_types = self.payload_types

        if mode == "tcp" and payload:
            for channel, frame in self.parser.feed(payload):
                if channel % 2 != 0:
                    self.forwarder.enqueue(frame, self.args.viewer_port + 1)
                    self.forwarder.stats.incr("rtcp")
                    continue

                if not is_valid_rtp(frame, payload_types):
                    continue
                pt = frame[1] & 0x7F
                is_audio = pt in self._audio_pts
                accepted, new_ssrc = self.ssrc.accept(frame, is_audio)
                if not accepted:
                    self.forwarder.stats.incr("filtered")
                    continue
                dst = self.args.viewer_port + 2 if is_audio else self.args.viewer_port
                self.forwarder.enqueue(frame, dst)
                self.forwarder.stats.incr("rtp")

                if new_ssrc is not None:
                    self.logger.log(
                        f"{Retro.SUCCESS}Locked SSRC 0x{new_ssrc:08x} "
                        f"(PT={pt}){Retro.RESET}"
                    )

        pkt.accept()

    def run(self) -> int:
        """
        Start orchestrator.

        Returns:
            0 if successfully; otherwise, returns 1.
        """
        if os.geteuid() != 0:
            print(f"{Retro.FAILED}Root privilege required.{Retro.RESET}", file=sys.stderr)
            return 1

        self._sysctl("net.core.rmem_max", "16777216")
        self._sysctl("net.core.rmem_default", "16777216")

        self.forwarder.open_socket()
        self.forwarder.start()

        if not self.iptables.setup():
            for e in self.iptables.drain_errors():
                print(f"{Retro.FAILED}{e}{Retro.RESET}", file=sys.stderr)
            self._teardown()
            return 1

        threading.Thread(
            target=self.ffplay.wait_and_launch,
            args=(lambda: self.transport_mode, lambda: self.real_sdp),
            daemon=True,
        ).start()

        nfq = NetfilterQueue()
        self.logger.info(f"{Retro.INFO}NFQUEUE listening on TCP port {self.args.rtsp_port}{Retro.RESET}")
        self.logger.info(f"{Retro.INFO}MITM: {self.args.server} <-> {self.args.client}{Retro.RESET}")
        self.logger.info(f"{Retro.INFO}Press Ctrl+C to exit.{Retro.RESET}\n")

        try:
            nfq.bind(QUEUE_NUM, self.process_packet)
            nfq.run()
        except KeyboardInterrupt:
            self.logger.info(f"\n{Retro.INFO}Shutting down...{Retro.RESET}")
        finally:
            try:
                nfq.unbind()
            except Exception:
                pass
            self._teardown()
        return 0

    def _teardown(self) -> None:
        """
        Terminate RTSP stream.
        """
        self._stop_flag.set()
        self.forwarder.stop()
        self.ffplay.terminate()
        self.iptables.cleanup()
        self.forwarder.close_socket()

        for line in self.forwarder.drain_logs():
            print(line)
        for line in self.ffplay.drain_events():
            print(line)

        snap = self.forwarder.stats.snapshot()
        print(
            f"{Retro.INFO}Stats: RTP={snap['rtp']} "
            f"Forwarded={snap['forwarded']} "
            f"Filtered={snap['filtered']} "
            f"Dropped={snap['dropped']}{Retro.RESET}"
        )
        print(f"{Retro.INFO}Cleanup complete.{Retro.RESET}")
