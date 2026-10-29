import argparse
import random
import time
import os

from core.scan import reporter
from core.scan import config as cf
from core.scan import workers
from utils import tui as u
from utils.net import is_host_reachable, classify_host_input
from utils.input_validate import parse_ports


def _clear_screen() -> None:
    """
    Cleaning screen
    """
    os.system("cls" if os.name == "nt" else "clear")

def register(subparsers) -> None:
    """
    Register the 'scan' subcommand into the given subparsers.
    """
    parser = subparsers.add_parser("scan", help="Scanner for RTSP open ports")

    parser.add_argument("-t", "--target", type=str, required=True,
                        help="IP/hostname of the target (can be separated by commas). Ex: 192.168.1.1,example.com")
    parser.add_argument("--port", type=str.lower, default="common",
                        help="Ports to be scanned. This value can be a single port, comma-separated list of ports, "
                             "a range of ports or pre-defined ports using 'common'. We can perform a full port scan by "
                             "specifying 'full'")
    parser.add_argument("-m", "--method", type=str.upper, default="DESCRIBE",
                        choices=["DESCRIBE", "OPTIONS", "SETUP", "PLAY", "PAUSE",
                                 "TEARDOWN", "GET_PARAMETER", "ANNOUNCE", "RECORD"],
                        help="RTSP method (Default: DESCRIBE)")
    parser.add_argument("--threads", type=int, default=cf.DEFAULT_THREADS,
                        help=f"Number of threads (Default: {cf.DEFAULT_THREADS})")
    parser.add_argument("--timeout", type=float, default=cf.DEFAULT_TIMEOUT,
                        help=f"Timeout in second (Default: {cf.DEFAULT_TIMEOUT})")
    parser.add_argument("--delay", type=float, default=cf.DEFAULT_DELAY,
                        help="Delay interval between requests (Default: 0)")
    parser.add_argument("--no-ping", action="store_true",
                        help="No sending ICMP requests to check reachable connections")
    parser.add_argument("-o", "--output", default=None, help="Save the output to TSV file")

def run(args) -> int:
    """
    Execute the scan subcommand.
    """
    targets = args.target.split(",")

    for t in targets:
        kind, err = classify_host_input(t)
        if kind == "invalid" or kind == "netmask":
            print(f"{u.Retro.FAILED}Invalid target {t}{u.Retro.RESET}")
            return 2

        if not args.no_ping:
           ok, reason, rtt = is_host_reachable(t)
           if ok:
               print(f"{u.Retro.SUCCESS}Host {t} is reachable{u.Retro.RESET}")
           else:
               print(f"{u.Retro.WARNING}Host {t} is unreachable. Reason: {reason}{u.Retro.RESET}")
               print(f"{u.Retro.WARNING}Attempt to scan without checking connection to {t}{u.Retro.RESET}")
        else:
            print(f"{u.Retro.WARNING}Attempt to scan without checking connection to {t}{u.Retro.RESET}")

    try:
        ports = []

        if args.port == 'full':
            print(f"{u.Retro.INFO}The value of --port is 'full'. Preparing to scan from port 1 to 65535{u.Retro.RESET}")
            ports = list(range(1, 65536))
        elif args.port == 'common':
            print(f"{u.Retro.INFO}The value of --port is 'common'. Preparing to scan ports {cf.COMMON_RTSP_PORTS}{u.Retro.RESET}")
            ports = cf.COMMON_RTSP_PORTS
        else:
            ports = parse_ports(args.port)
    except ValueError as e:
        print(f"{u.Retro.FAILED}{e}{u.Retro.RESET}")
        return 2

    if args.threads < 1:
        print(f"{u.Retro.FAILED}--threads must be >= 1{u.Retro.RESET}")
        return 2

    if args.timeout <= 0:
        print(f"{u.Retro.FAILED}--timeout must be > 0{u.Retro.RESET}")
        return 2

    if args.delay < 0:
        print(f"{u.Retro.FAILED}--delay must be >= 0{u.Retro.RESET}")
        return 2

    time.sleep(2)
    _clear_screen()

    u.print_banner(f"{cf.DEFAULT_BANNER}", typing=True, subtitle=cf.SUBTITLE)
    print(u.colorize(f"SETTINGS RECEIVED".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(random.randint(60, 100))

    print(f"  {'Target':<11}: {u.colorize(args.target, u.Retro.NEON_GREEN)}")
    print(f"  {'Port':<11}: {u.colorize(args.port, u.Retro.NEON_GREEN)}")
    print(f"  {'Method':<11}: {u.colorize(args.method, u.Retro.NEON_GREEN)}")
    print(f"  {'Threads':<11}: {u.colorize(str(args.threads), u.Retro.NEON_GREEN)}")
    print(f"  {'Delay':<11}: {u.colorize(str(args.delay) + 's', u.Retro.NEON_GREEN)}")
    print(f"  {'Timeout':<11}: {u.colorize(str(args.timeout) + 's', u.Retro.NEON_GREEN)}")
    print()

    u.print_retro_divider(random.randint(60, 100))

    try:
        results = workers.start_scan(targets, ports, method=args.method, timeout=args.timeout,
                                     delay=args.delay, n_threads=args.threads)
    except KeyboardInterrupt:
        print(f"\n\n{u.Retro.WARNING}Stopped by Ctrl+C..{u.Retro.RESET}")
        print(f"{u.Retro.WARNING}Cleaning threads...{u.Retro.RESET}")
        return 130

    print(u.colorize(f"SUMMARY".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(random.randint(60, 100))

    reporter.report_scan_results(
        results=results,
        targets=targets,
        output_file=args.output
    )

    return 0
