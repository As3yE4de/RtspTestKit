import argparse
import random
import sys
import time
import os
import re

from core.relay import config as cf
from core.relay.orchestrator import RtspTap
from utils import tui as u
from utils.input_validate import *


_IPV4_LIKE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


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
    parser.add_argument("--rtsp-port", type=int, default=None,
                        help=f"Server's RTSP port (Default: {cf.DEFAULT_RTSP_PORT})")
    parser.add_argument("--viewer-port", type=int, default=None,
                        help=f"Port for local player to display stream (Default: {cf.DEFAULT_VIEWER_PORT})")
    parser.add_argument("-i","--iface", default=cf.DEFAULT_IFACE,
                        help="Network interface for NFQUEUE / IP forwarding")
    parser.add_argument("-c","--client", default=None, required=True,
                        help="IP or hostname of RTSP client")
    parser.add_argument("-s","--server", default=None, required=True,
                        help="IP or hostname of RTSP server")
    parser.add_argument("--debug", action="store_true",
                        help="Detailed logs")

def run(args) -> int:
    """
    Execute the relay subcommand (placeholder).
    """
    if args.rtsp_port is None:
        args.rtsp_port = cf.DEFAULT_RTSP_PORT
    elif not is_a_single_port(args.rtsp_port):
        print(f"{u.Retro.FAILED}Invalid port '{args.rtsp_port}'{u.Retro.RESET}")
        return 2

    if args.viewer_port is None:
        args.viewer_port = cf.DEFAULT_VIEWER_PORT
    elif not is_a_single_port(args.viewer_port):
        print(f"{u.Retro.FAILED}Invalid port '{args.viewer_port}'{u.Retro.RESET}")
        return 2

    if _IPV4_LIKE.match(args.client) is not None:
        if not is_a_single_ipv4(args.client):
            print(f"{u.Retro.FAILED}Invalid client '{args.client}'{u.Retro.RESET}")
            return 2
    else:
         if not is_a_single_hostname(args.client):
            print(f"{u.Retro.FAILED}Invalid client '{args.target}'{u.Retro.RESET}")
            return 2

    if _IPV4_LIKE.match(args.server) is not None:
        if not is_a_single_ipv4(args.server):
            print(f"{u.Retro.FAILED}Invalid server '{args.server}'{u.Retro.RESET}")
            return 2
    else:
         if not is_a_single_hostname(args.target):
            print(f"{u.Retro.FAILED}Invalid server '{args.server}'{u.Retro.RESET}")
            return 2

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
