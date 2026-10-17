#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-}"
[[ -z "$IFACE" ]] && exit 1

# Lưu trạng thái ip_forward trước khi bật
current=$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo 0)
echo "$current" > /tmp/rtsprelay_ip_forward_saved

if ! sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1; then
    echo "failed to enable ip_forward" >&2
    exit 1
fi

sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null 2>&1 || true
sysctl -w net.ipv4.conf.default.rp_filter=0 >/dev/null 2>&1 || true
RP_PATH="/proc/sys/net/ipv4/conf/$IFACE/rp_filter"
if [[ -f "$RP_PATH" ]]; then
    sysctl -w "net.ipv4.conf.$IFACE.rp_filter=0" >/dev/null 2>&1 || true
fi

# Dùng -A (append) thay vì -I (insert) để không đẩy rule lên trước NFQUEUE
if ! iptables -w -C FORWARD -i "$IFACE" -o "$IFACE" -j ACCEPT 2>/dev/null; then
    iptables -w -A FORWARD -i "$IFACE" -o "$IFACE" -j ACCEPT
fi

exit 0
