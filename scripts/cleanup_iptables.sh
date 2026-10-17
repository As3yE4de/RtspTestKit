#!/usr/bin/env bash
set -uo pipefail

IFACE="${1:-}"
[[ -z "$IFACE" ]] && exit 1

while iptables -w -C FORWARD -i "$IFACE" -o "$IFACE" -j ACCEPT 2>/dev/null; do
    iptables -w -D FORWARD -i "$IFACE" -o "$IFACE" -j ACCEPT || break
done

# Khôi phục trạng thái ip_forward đã lưu
if [[ -f /tmp/rtsprelay_ip_forward_saved ]]; then
    saved=$(cat /tmp/rtsprelay_ip_forward_saved)
    sysctl -w net.ipv4.ip_forward="$saved" >/dev/null 2>&1 || true
    rm -f /tmp/rtsprelay_ip_forward_saved
fi

sysctl -w net.ipv4.conf.all.rp_filter=1 >/dev/null 2>&1 || true
sysctl -w net.ipv4.conf.default.rp_filter=1 >/dev/null 2>&1 || true
sysctl -w "net.ipv4.conf.$IFACE.rp_filter=1" >/dev/null 2>&1 || true

exit 0
