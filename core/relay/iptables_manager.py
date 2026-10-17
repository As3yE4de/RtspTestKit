from __future__ import annotations
from pathlib import Path
import subprocess

from core.relay.config import QUEUE_NUM

class IptablesManager:
    SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"

    def __init__(self, iface: str, rtsp_port: int) -> None:
        """
        Initializer
        """
        self.iface = iface
        self.rtsp_port = rtsp_port
        self._installed_udp_ports = set()
        self._rtsp_rules_installed = False
        self._forward_enabled = False
        self._errors = []

    @staticmethod
    def _run(cmd: list[str]) -> bool:
        """
        Execute iptables command line.

        Args:
            cmd: iptables command in list

        Returns:
            True if the command executed successfully; otherwise, returns False.
        """
        try:
            r = subprocess.run(cmd, check=False, capture_output=True)
            return r.returncode == 0
        except Exception:
            return False

    def _iptables(self, *args: str) -> bool:
        """
        Wrapper function for iptables.

        Args:
            *args: Extra arguments for iptables command.

        Returns:
            True if _run() function runs successfully; otherwise, returns False.
        """
        return self._run(["iptables", *args])

    def _iptables_check(self, *args: str) -> bool:
        """
        Check whether an iptables rule exists (using -C).

        Args:
            *args: Rule spec (without -C).

        Returns:
            True if the rule exists; otherwise, returns False.
        """
        return self._run(["iptables", "-C", *args])

    def _iptables_delete(self, *args: str) -> bool:
        """
        Delete an iptables rule only if it exists.

        Args:
            *args: Rule spec (without -D).

        Returns:
            True if the rule was deleted or did not exist; otherwise, returns False.
        """
        if not self._iptables_check(*args):
            return True
        return self._iptables("-D", *args)

    def _iptables_insert(self, *args: str) -> bool:
        """
        Insert an iptables rule only if it does not already exist.

        Args:
            *args: Rule spec (without -I).

        Returns:
            True if the rule was inserted or already existed; otherwise, returns False.
        """
        if self._iptables_check(*args):
            return True
        return self._iptables("-I", *args)

    def _run_script(self, script_name: str) -> bool:
        """
        Execute external bash script.

        Args:
            script_name: Name of the bash script

        Returns:
            True if the script executed successfully; otherwise, returns False.
        """
        script_path = self.SCRIPTS_DIR / script_name
        if not script_path.exists():
            self._errors.append(f"Missing script: {script_path}")
            return False
        try:
            r = subprocess.run(
                ["bash", str(script_path), self.iface],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
            return r.returncode == 0
        except Exception as e:
            self._errors.append(f"Script {script_name} failed: {e}")
            return False

    def install_rtsp_rules(self) -> bool:
        """
        Add NFQUEUE rule for RTSP port (bidirectional).

        Returns:
            True if adding successfully; otherwise, returns False.
        """
        ok1 = self._iptables_insert(
            "FORWARD",
            "-p", "tcp", "--dport", str(self.rtsp_port),
            "-j", "NFQUEUE",
            "--queue-num", str(QUEUE_NUM),
            "--queue-bypass",
        )
        ok2 = self._iptables_insert(
            "FORWARD",
            "-p", "tcp", "--sport", str(self.rtsp_port),
            "-j", "NFQUEUE",
            "--queue-num", str(QUEUE_NUM),
            "--queue-bypass",
        )

        self._rtsp_rules_installed = ok1 and ok2
        if not self._rtsp_rules_installed:
            self._errors.append(f"Failed to install RTSP NFQUEUE rules")
        return self._rtsp_rules_installed

    def remove_rtsp_rules(self) -> bool:
        """
        Clean up iptables rules.

        Returns:
            True if cleaning up successfully; otherwise, returns False.
        """
        ok1 = self._iptables_delete(
            "FORWARD",
            "-p", "tcp", "--dport", str(self.rtsp_port),
            "-j", "NFQUEUE",
            "--queue-num", str(QUEUE_NUM),
            "--queue-bypass",
        )
        ok2 = self._iptables_delete(
            "FORWARD",
            "-p", "tcp", "--sport", str(self.rtsp_port),
            "-j", "NFQUEUE",
            "--queue-num", str(QUEUE_NUM),
            "--queue-bypass",
        )

        self._rtsp_rules_installed = False
        return ok1 and ok2

    def install_udp_rule(self, port: int) -> bool:
        """
        Add NFQUEUE rule for UDP destination port.

        Args:
            port: Destination port

        Returns:
            True if adding successfully; otherwise, returns False.
        """
        if port in self._installed_udp_ports:
            return True

        spec = (
            "FORWARD",
            "-p", "udp", "--dport", str(port),
            "-j", "NFQUEUE",
            "--queue-num", str(QUEUE_NUM),
            "--queue-bypass",
        )
        if self._iptables_check(*spec):
            self._installed_udp_ports.add(port)
            return True

        ok = self._iptables_insert(*spec)

        if ok:
            self._installed_udp_ports.add(port)
        else:
            self._errors.append(f"Failed to install UDP NFQUEUE rule for port {port}")
        return ok

    def remove_all_udp_rules(self) -> int:
        """
        Remove all dynamic UDP rules.

        Returns:
            Number of rules which are removed successfully.
        """
        removed = 0
        for port in list(self._installed_udp_ports):
            spec = (
                "FORWARD",
                "-p", "udp", "--dport", str(port),
                "-j", "NFQUEUE",
                "--queue-num", str(QUEUE_NUM),
                "--queue-bypass",
            )
            if self._iptables_delete(*spec):
                removed += 1
            self._installed_udp_ports.discard(port)

        return removed

    def setup(self) -> bool:
        """
        Set up iptables rules globally.

        Returns:
            True if setup_iptables.sh executed successfully; otherwise, returns False.
        """
        if not self._run_script("setup_iptables.sh"):
            self._errors.append("setup_iptables.sh failed")
            return False
        self._forward_enabled = True

        if not self.install_rtsp_rules():
            self._run_script("cleanup_iptables.sh")
            self._forward_enabled = False
            return False

        return True

    def cleanup(self) -> bool:
        """
        Clean up iptables rules globally.

        Returns:
            True if cleanup_iptables.sh executed successfully; otherwise, returns False.
        """
        ok_rtsp = self.remove_rtsp_rules()
        self.remove_all_udp_rules()
        ok_script = self._run_script("cleanup_iptables.sh")

        self._forward_enabled = False

        if not ok_script:
            self._errors.append(f"cleanup_iptables.sh failed")
        return ok_rtsp and ok_script

    def drain_errors(self) -> list[str]:
        """
        Receive and clean up error logs.

        Returns:
            Error logs in list.
        """
        errs, self._errors = self._errors, []
        return errs

    @property
    def installed_udp_ports(self) -> set[int]:
        return set(self._installed_udp_ports)

    @property
    def rtsp_rules_installed(self) -> bool:
        return self._rtsp_rules_installed
