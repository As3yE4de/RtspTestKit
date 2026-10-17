from main.commands import enum_cmd, relay_cmd


def dispatch(subparsers) -> None:
    """
    Register all subcommands.
    """
    enum_cmd.register(subparsers)
    relay_cmd.register(subparsers)
