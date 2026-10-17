from queue import Empty
from core.enumerator import config as cf
from core.enumerator import workers
from core.enumerator import wordlist_handler as w_handler
from core.enumerator import reporter as rp
from utils import tui as u

import argparse
import random


def register(subparsers) -> None:
    """
    Register the 'enum' subcommand into the given subparsers.
    """
    parser = subparsers.add_parser("enum", help="RTSP path enumeration")

    parser.add_argument("-t", "--target", required=True, help="IP or hostname of the target")
    parser.add_argument("-p", "--port", type=int, default=None,
                        help=f"RTSP port (Default: {cf.DEFAULT_RTSP_PORT}, "
                             f"or {cf.DEFAULT_RTSPS_PORT} with --tls)")
    parser.add_argument("-w", "--wordlist", required=True, help="Wordlist file of RTSP paths")
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
    parser.add_argument("--tls", action="store_true", help="Use RTSPS (TLS)")
    parser.add_argument("-o", "--output", default=None, help="Save the output to TSV file")
    parser.add_argument("-v", "--verbose", action="store_true", help="More error details")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--found-only", action="store_true",
                        help="Only print existing paths (200/401/403/454/455)")
    parser.add_argument("-U", "--username", default=None, help="Username for RTSP authentication")
    parser.add_argument("-P", "--password", default=None, help="Password for RTSP authentication")


def run(args) -> int:
    """
    Execute the enum subcommand.
    """
    if args.threads < 1:
        print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}--threads must be >= 1")
        return 2

    if args.timeout <= 0:
        print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}--timeout must be > 0")
        return 2

    if args.delay < 0:
        print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}--delay must be >= 0")
        return 2

    if args.username is not None:
        if args.password is None:
            print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_YELLOW}WARNING{u.Retro.DEEP_PURP}] "
                  f"{u.Retro.CYAN}Password is not provided.")
            print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_YELLOW}WARNING{u.Retro.DEEP_PURP}] "
                  f"{u.Retro.CYAN}Attempt to log in with blank password.")
            args.password = ""
        if args.method != "DESCRIBE":
            print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_YELLOW}WARNING{u.Retro.DEEP_PURP}] "
                  f"{u.Retro.CYAN}Auth mode forces method to DESCRIBE "
                  f"(was: {args.method}).")
        args.method = "DESCRIBE"

    if args.username is None and args.password is not None:
        print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}Must provide username along with password.")
        return 1

    if args.no_color:
        u.COLOR_ENABLED = False

    if args.port is None:
        args.port = cf.DEFAULT_RTSPS_PORT if args.tls else cf.DEFAULT_RTSP_PORT

    try:
        raw_paths = w_handler.load_url_pathlist(args.wordlist)
    except OSError as e:
        print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}Cannot read wordlist: {e}")
        return 1

    if not raw_paths:
        print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}Wordlist is empty.")
        return 1

    normalized_paths = w_handler.dedupe_url_paths(raw_paths)

    divider_w = random.randint(60, 100)

    u.print_banner(f"{cf.DEFAULT_BANNER}", typing=True, subtitle=cf.SUBTITLE)
    print(u.colorize(f"SETTINGS RECEIVED".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(divider_w)

    print(f"  {'Target':<11}: {u.colorize(args.target + ':' + str(args.port), u.Retro.NEON_GREEN)}")
    print(f"  {'Method':<11}: {u.colorize(args.method, u.Retro.NEON_GREEN)}")
    print(f"  {'TLS':<11}: {u.colorize(str(args.tls), u.Retro.NEON_GREEN)}")
    print(f"  {'Paths':<11}: {u.colorize(str(len(normalized_paths)) + ' (duplicates removed)', u.Retro.NEON_GREEN)}")
    print(f"  {'Threads':<11}: {u.colorize(str(args.threads), u.Retro.NEON_GREEN)}")
    print(f"  {'Delay':<11}: {u.colorize(str(args.delay) + 's', u.Retro.NEON_GREEN)}")
    print(f"  {'Found only':<11}: {u.colorize(str(args.found_only), u.Retro.NEON_GREEN)}")
    print(f"  {'Username':<11}: {u.colorize(str(args.username), u.Retro.NEON_GREEN)}")
    print(f"  {'Password':<11}: {u.colorize(args.password, u.Retro.NEON_GREEN)}")
    print()

    u.print_retro_divider(divider_w)

    header = (f"{'METHOD':<9} {'PATH':<75} {'SYMBOL':<15} "
              f"{'STATUS':<6} {'TIME':>10} {'NOTE'}")
    print(u.colorize(header, u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(divider_w)

    result_queue, threads = workers.start_probe(
        normalized_paths, host=args.target, port=args.port,
        method=args.method, timeout=args.timeout,
        use_tls=args.tls, delay=args.delay, n_threads=args.threads,
        username=args.username, password=args.password,
    )

    out_fh = None
    if args.output:
        try:
            out_fh = open(args.output, "w", encoding="utf-8")
            out_fh.write("method\tpath\tstatus\ttime\treason\terror\n")
        except OSError as e:
            print(f"{u.Retro.DEEP_PURP}[{u.Retro.NEON_RED}FAILED{u.Retro.DEEP_PURP}] "
                  f"{u.Retro.CYAN}Cannot open output file: {e}")
            return 1

    st = rp.Stats()
    interrupted = False
    try:
        while any(t.is_alive() for t in threads) or not result_queue.empty():
            try:
                result = result_queue.get(timeout=0.1)
            except Empty:
                continue

            st.update(result)

            if not args.found_only or result["status"] in cf.FOUND_STATUSES:
                rp.print_result(result, args.verbose)

            if out_fh:
                rp.write_result(out_fh, result)
    except KeyboardInterrupt:
        interrupted = True
        print(f"\n{u.Retro.DEEP_PURP}[{u.Retro.NEON_YELLOW}WARNING{u.Retro.DEEP_PURP}] "
              f"{u.Retro.CYAN}Stopped by Ctrl+C. Waiting for workers...")
    finally:
        if out_fh:
            out_fh.close()

    if interrupted:
        for t in threads:
            t.join(timeout=0.5)

    u.print_retro_divider(divider_w)

    print(u.colorize(f"SUMMARY".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(divider_w)

    print(st.summary())
    return 130 if interrupted else 0
