from version import __version__
from main.commands import dispatch, enum_cmd, relay_cmd, brute_cmd

import argparse


def build_parser() -> argparse.ArgumentParser:
    """
    Build the top-level argument parser with subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="rtsp_tk",
        description="RTSP Test Kit - Penetration Testing Tool for RTSP Service",
    )
    parser.add_argument("--version", action="version", version=f"RtspTestKit {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)
    dispatch(subparsers)

    return parser


def main(argv=None) -> int:
    """
    Entry point. Parse argv and dispatch to the correct subcommand.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "enum":
        return enum_cmd.run(args)
    if args.command == "relay":
        return relay_cmd.run(args)
    if args.command == "brute":
        return brute_cmd.run(args)

    parser.print_help()
    return 2
