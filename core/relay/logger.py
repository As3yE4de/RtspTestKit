from __future__ import annotations


class Logger:
    def __init__(self, debug: bool = False) -> None:
        """
        Initializer
        """
        self.debug = debug

    def log(self, msg: str) -> None:
        """
        Print message to consosle when debugging is enabled.

        Args:
            msg: Message string
        """
        if self.debug:
            print(msg, flush=True)

    def info(self, msg: str) -> None:
        """
        Print message to console .

        Args:
            msg: Message string
        """
        print(msg, flush=True)
