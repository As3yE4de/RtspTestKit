import argparse
import random
import sys
import time
import os

from core.relay import config as cf
from core.relay.orchestrator import RtspTap
from utils import tui as u


def _clear_screen() -> None:
    """
    Cleaning screen
    """
    os.system("cls" if os.name == "nt" else "clear")

def register(subparsers) -> None:
    """
    Register the 'relay' subcommand into the given subparsers.
    """
    parser = subparsers.add_parser("relay", help="Real-time RTSP MITM Tap for stream relaying")
    parser.add_argument("--rtsp-port", type=int, default=cf.DEFAULT_RTSP_PORT, help="Server's RTSP port")
    parser.add_argument("--viewer-port", type=int, default=cf.DEFAULT_VIEWER_PORT, help="Port for local player to display stream")
    parser.add_argument("-i","--iface", default=cf.DEFAULT_IFACE, help="Network interface for NFQUEUE / IP forwarding")
    parser.add_argument("-c","--client", default=None, required=True, help="IP or hostname of RTSP client")
    parser.add_argument("-s","--server", default=None, required=True, help="IP or hostname of RTSP server")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--debug", action="store_true", help="Detailed logs")

def run(args) -> int:
    """
    Execute the relay subcommand (placeholder).
    """
    if args.no_color:
        u.set_color_enabled(False)

    time.sleep(2)
    _clear_screen()

    u.print_banner(f"{cf.DEFAULT_BANNER}", typing=True, subtitle=cf.SUBTITLE)
    print(u.colorize(f"SETTINGS RECEIVED".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(random.randint(60,100))

    print(f"  {'RTSP server':<14}: {u.colorize(args.server + ':' + str(args.rtsp_port), u.Retro.NEON_GREEN)}")
    print(f"  {'RTSP client':<14}: {u.colorize(args.client, u.Retro.NEON_GREEN)}")
    print(f"  {'Stream Player':<14}: {u.colorize(cf.VIEWER_HOST + ':' + str(args.viewer_port), u.Retro.NEON_GREEN)}")
    print()

    u.print_retro_divider(random.randint(60,100))

    tap = RtspTap(args)
    return tap.run()
