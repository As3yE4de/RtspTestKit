#!/usr/bin/env bash

set -uo pipefail

RESET="\033[0m"
DEEP_PURP="\033[38;5;93m"
NEON_RED="\033[38;5;196m"
NEON_GREEN="\033[38;5;46m"
NEON_BLUE="\033[38;5;27m"
NEON_YELLOW="\033[38;5;226m"
CYAN="\033[38;5;51m"

ok()   { echo -e "${DEEP_PURP}[${NEON_GREEN}SUCCESS${DEEP_PURP}]${NEON_GREEN} $*${RESET}"; }
err()  { echo -e "${DEEP_PURP}[${NEON_RED}FAILED${DEEP_PURP}]${NEON_RED} $*${RESET}"; }
warn() { echo -e "${DEEP_PURP}[${NEON_YELLOW}WARNING${DEEP_PURP}]${CYAN} $*${RESET}"; }
info() { echo -e "${DEEP_PURP}[${NEON_BLUE}INFO${DEEP_PURP}]${CYAN} $*${RESET}"; }

if [[ $EUID -ne 0 ]]; then
    err "Root privilege required. Run: sudo ./install.sh"
    exit 1
fi

if ! command -v apt-get &>/dev/null; then
    err "Only Debian/Ubuntu supported by this script"
    exit 1
fi

PKG_MGR="apt-get"
command -v apt &>/dev/null && PKG_MGR="apt"

info "Updating apt package index..."
if ! $PKG_MGR update -qq; then
    err "apt update failed"
    exit 1
fi
ok "apt index updated"

info "Installing system packages..."
PKGS=(
    python3
    python3-pip
    python3-venv
    python3-netfilterqueue
    python3-scapy
    iptables
    ffmpeg
)

if ! $PKG_MGR install -y "${PKGS[@]}"; then
    err "Failed to install one or more packages: ${PKGS[*]}"
    exit 1
fi
ok "System packages installed"

if ! python3 -c "from netfilterqueue import NetfilterQueue" &>/dev/null; then
    err "Cannot import NetfilterQueue"
    err "Try: sudo apt install python3-netfilterqueue"
    exit 1
fi
ok "NetfilterQueue module available"

if ! python3 -c "from scapy.all import IP" &>/dev/null; then
    warn "scapy not available via apt, trying pip..."
    if ! pip3 install --break-system-packages scapy 2>/dev/null && \
       ! pip3 install scapy; then
        err "Cannot install scapy"
        exit 1
    fi
    if ! python3 -c "from scapy.all import IP" &>/dev/null; then
        err "scapy still not importable after pip install"
        exit 1
    fi
fi
ok "scapy module available"

if ! command -v ffplay &>/dev/null; then
    err "ffplay not found (part of ffmpeg)"
    exit 1
fi
ok "ffplay available"

if ! command -v iptables &>/dev/null; then
    err "iptables not found"
    exit 1
fi
ok "iptables available"

info "Loading kernel modules..."
modprobe nfnetlink_queue 2>/dev/null && ok "nfnetlink_queue loaded" || warn "nfnetlink_queue may be built-in"
modprobe iptable_nat     2>/dev/null && ok "iptable_nat loaded"      || warn "iptable_nat may be built-in"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR"

MISSING=()
for f in setup_iptables.sh cleanup_iptables.sh; do
    [[ ! -f "$SCRIPTS_DIR/$f" ]] && MISSING+=("$f")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    err "Missing iptables scripts: ${MISSING[*]}"
    err "Expected in: $SCRIPTS_DIR"
    exit 1
fi

chmod +x "$SCRIPTS_DIR/"*.sh
ok "iptables scripts found and executable"

echo
ok "Installation complete. Ready to use."
echo
info "Remember to run ARP spoofing externally before starting module relay."
