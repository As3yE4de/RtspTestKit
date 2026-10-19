from queue import Empty
import argparse
import random

from core.bruteforce import config as cf
from core.bruteforce import workers
from utils import tui as u
from utils import file as f
from utils.rtsp_parse import create_url


def register(subparsers) -> None:
    """
    Register the 'brute' subcommand into the given subparsers.
    """
    parser = subparsers.add_parser("brute", help="Brute-forcing RTSP credentials")

    parser.add_argument("-t", "--target", required=True, help="IP or hostname of the server")
    parser.add_argument("-p", "--port", type=int, default=cf.DEFAULT_RTSP_PORT,
                        help=f"RTSP port (Default: {cf.DEFAULT_RTSP_PORT}, "
                             f"or {cf.DEFAULT_RTSPS_PORT} with --tls)")
    parser.add_argument("--path", required=True, help="Valid RTSP path on the server")
    parser.add_argument("--threads", type=int, default=cf.DEFAULT_THREADS,
                        help=f"Number of threads (Default: {cf.DEFAULT_THREADS})")
    parser.add_argument("--timeout", type=float, default=cf.DEFAULT_TIMEOUT,
                        help=f"Timeout in second (Default: {cf.DEFAULT_TIMEOUT})")
    parser.add_argument("--delay", type=float, default=cf.DEFAULT_DELAY,
                        help=f"Delay interval between requests (Default: {cf.DEFAULT_DELAY})")
    parser.add_argument("--tls", action="store_true", help="Use RTSPS (TLS)")
    parser.add_argument("-o", "--output", default=None, help="Save the output to TSV file")
    parser.add_argument("-v", "--verbose", action="store_true", help="More error details")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--stop-on-succeed", action="store_true", help="Stop brute-forcing when a valid credential found")
    parser.add_argument("-U", "--username", default=None, help="Username for RTSP authentication")
    parser.add_argument("--user-file", default=None, help="Wordlist of usernames for RTSP authentication")
    parser.add_argument("-P", "--password", default=None, help="Password for RTSP authentication")
    parser.add_argument("--pass-file", default=None, help="Wordlist of passwords for RTSP authentication")

def run(args) -> int:
    """
    Execute the brute subcommand.
    """
    if not args.path or not args.path.strip():
        print(f"{u.Retro.FAILED}--path must not be empty{u.Retro.RESET}")
        return 2

    if not args.path.startswith("/"):
        print(f"{u.Retro.FAILED}--path must start with '/'. Got: {args.path!r}{u.Retro.RESET}")
        return 2

    args.path = args.path.strip()

    if args.threads < 1:
        print(f"{u.Retro.FAILED}--threads must be >= 1{u.Retro.RESET}")
        return 2

    if args.timeout <= 0:
        print(f"{u.Retro.FAILED}--timeout must be > 0{u.Retro.RESET}")
        return 2

    if args.delay < 0:
        print(f"{u.Retro.FAILED}--delay must be >= 0{u.Retro.RESET}")
        return 2

    if args.username is not None and args.user_file is not None:
        print(f"{u.Retro.FAILED}Cannot use -U/--username together with --user-file{u.Retro.RESET}")
        return 1

    if args.password is not None and args.pass_file is not None:
        print(f"{u.Retro.FAILED}Cannot use -P/--password together with --pass-file{u.Retro.RESET}")
        return 1

    if args.username is not None:
        usernames = [args.username]
    elif args.user_file is not None:
        usernames = f.load_stripped_lines(args.user_file)
        if not usernames:
            print(f"{u.Retro.FAILED}Cannot read or empty --user-file: {args.user_file}{u.Retro.RESET}")
            return 1
    else:
        usernames = []

    if args.password is not None:
        passwords = [args.password]
    elif args.pass_file is not None:
        passwords = f.load_password_lines(args.pass_file)
        if not passwords:
            print(f"{u.Retro.FAILED}Cannot read or empty --pass-file: {args.pass_file}{u.Retro.RESET}")
            return 1
    else:
        passwords = []

    if usernames and not passwords:
        print(f"{u.Retro.WARNING}Password is not provided{u.Retro.RESET}")
        print(f"{u.Retro.WARNING}Attempt to log in with blank password{u.Retro.RESET}")
        passwords = [""]

    if passwords and not usernames:
        print(f"{u.Retro.FAILED}Must provide username (-U/--username or --user-file) along with password{u.Retro.RESET}")
        return 1

    if not usernames and not passwords:
        print(f"{u.Retro.FAILED}No credentials provided. Use -U/-P, -U/--pass-file, --user-file/-P, or --user-file/--pass-file{u.Retro.RESET}")
        return 1

    if args.no_color:
        u.COLOR_ENABLED = False

    if args.port is None:
        args.port = cf.DEFAULT_RTSPS_PORT if args.tls else cf.DEFAULT_RTSP_PORT

    u.print_banner(f"{cf.DEFAULT_BANNER}", typing=True, subtitle=cf.SUBTITLE)
    print(u.colorize(f"SETTINGS RECEIVED".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(random.randint(60, 100))

    print(f"  {'Target':<16}: {u.colorize(args.target + ':' + str(args.port), u.Retro.NEON_GREEN)}")
    print(f"  {'Stream path':<16}: {u.colorize(args.path, u.Retro.NEON_GREEN)}")
    print(f"  {'TLS':<16}: {u.colorize(str(args.tls), u.Retro.NEON_GREEN)}")
    print(f"  {'Threads':<16}: {u.colorize(str(args.threads), u.Retro.NEON_GREEN)}")
    print(f"  {'Timeout':<16}: {u.colorize(str(args.timeout) + 's', u.Retro.NEON_GREEN)}")
    print(f"  {'Delay':<16}: {u.colorize(str(args.delay) + 's', u.Retro.NEON_GREEN)}")
    print(f"  {'Username':<16}: {u.colorize(str(args.username), u.Retro.NEON_GREEN)}")
    print(f"  {'Password':<16}: {u.colorize(args.password, u.Retro.NEON_GREEN)}")
    print(f"  {'User file':<16}: {u.colorize(args.user_file, u.Retro.NEON_GREEN)}")
    print(f"  {'Password file':<16}: {u.colorize(args.pass_file, u.Retro.NEON_GREEN)}")
    print(f"  {'Stop on succeed':<16}: {u.colorize(args.stop_on_succeed, u.Retro.NEON_GREEN)}")
    print()

    u.print_retro_divider(random.randint(60, 100))

    credentials: list[tuple[str, str]] = [
        (user, pwd) for user in usernames for pwd in passwords
    ]
    total = len(credentials)

    header = (f"{'STATUS':<10} {'CREDENTIAL':<40} {'MESSAGE':<20} "
              f"{u.colorize(f'(Total credentials: {total})', u.Retro.HOT_PINK)}")

    print(u.colorize(header, u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(random.randint(60, 100))

    rtsp_url = create_url(args.target, args.port, args.path, args.tls)

    out_fp = None
    if args.output:
        try:
            out_fp = open(args.output, "a", encoding="utf-8")
            if out_fp.tell() == 0:
                out_fp.write("username\tpassword\turl\tresult\n")
        except OSError as e:
            print(f"{u.Retro.FAILED}Cannot open output file: {e}{u.Retro.RESET}")
            return 1

    result_queue, threads, stop_event = workers.start_brute(
        url=rtsp_url,
        credentials=credentials,
        method="DESCRIBE",
        timeout=args.timeout,
        use_tls=args.tls,
        delay=args.delay,
        n_threads=args.threads,
        stop_on_succeed=args.stop_on_succeed,
    )

    found: list[tuple[str, str]] = []
    checked = 0
    interrupted = False

    try:
        while True:
            try:
                res: dict = result_queue.get(timeout=0.5)
            except Empty:
                if not any(t.is_alive() for t in threads):
                    break
                continue

            checked += 1
            username: str = res["username"]
            password: str = res["password"]
            ok: bool = res["ok"]
            message: str = res["message"]

            if ok:
                tag = f"{u.Retro.SUCCESS} "
            else:
                tag = f"{u.Retro.FAILED}  "

            raw_cred = f"{username}:{password}"
            if len(raw_cred) > 30:
                raw_cred = raw_cred[:27] + "..."

            msg = f"({message})"

            if ok:
                print(f"{tag} {raw_cred:<40} {msg:<20}")

                found.append((username, password))
                if out_fp:
                    out_fp.write(f"{username}\t{password}\t{rtsp_url}\tOK\n")
                    out_fp.flush()

            elif args.verbose:
                print(f"{tag} {raw_cred:<40} {msg:<20}")

            elif checked % 50 == 0:
                print(f"{u.Retro.INFO}Progress: {checked}/{total}{u.Retro.RESET}")

    except KeyboardInterrupt:
        print(f"\n{u.Retro.WARNING}Interrupted by user. Stopping...{u.Retro.RESET}")
        interrupted = True
        stop_event.set()

    for t in threads:
        t.join(timeout=2)

    if out_fp:
        out_fp.close()

    print()
    u.print_retro_divider(random.randint(60, 100))
    print(u.colorize(f"SUMMARY".center(30, " "), u.Retro.HOT_PINK + u.Retro.BOLD))
    u.print_retro_divider(random.randint(60, 100))
    if found:
        print(u.colorize("  VALID CREDENTIALS  ", u.Retro.NEON_GREEN + u.Retro.BOLD))
        for user, pwd in found:
            print(f"  {u.colorize(f'{user}:{pwd}', u.Retro.NEON_GREEN)}")
    else:
        print(u.colorize("  NO VALID CREDENTIALS  ", u.Retro.NEON_RED + u.Retro.BOLD))
    print()
    print(f"  Tried {u.colorize(f'{checked}/{total}', u.Retro.CYAN)} credential(s).")

    if interrupted:
        return 130
    return 0 if found else 1
