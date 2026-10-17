from __future__ import annotations
import socket
import struct


def _ip_checksum(data: bytes) -> int:
    """
    Calculate 16-bit Internet checksum .

    Args:
        data: Packet in byte

    Returns:
        Checksum in hexadecimal.
    """
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


def build_ip_udp(src_ip: str, dst_ip: str, src_port: int,
                 dst_port: int, payload: bytes) -> bytes:
    """
    Create a IPv4 packet containing UDP datagram.

    Args:
        src_ip: Source IP address
        dst_ip: Destination IP address
        src_port: Source port
        dst_port: Destination port
        payload: data

    Returns:
        A complete IP/UDP packet in byte.
    """
    udp_len = 8 + len(payload)
    udp_hdr = struct.pack("!HHHH", src_port, dst_port, udp_len, 0)
    pseudo = struct.pack(
        "!4s4sBBH",
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
        0, socket.IPPROTO_UDP, udp_len,
    )
    udp_cksum = _ip_checksum(pseudo + udp_hdr + payload)
    udp_hdr = struct.pack("!HHHH", src_port, dst_port, udp_len, udp_cksum)

    total_len = 20 + udp_len
    ip_hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, total_len, 0, 0, 64,
        socket.IPPROTO_UDP, 0,
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
    )
    ip_cksum = _ip_checksum(ip_hdr)
    ip_hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, total_len, 0, 0, 64,
        socket.IPPROTO_UDP, ip_cksum,
        socket.inet_aton(src_ip),
        socket.inet_aton(dst_ip),
    )
    return ip_hdr + udp_hdr + payload


def init_raw_socket(sndbuf: int) -> socket.socket:
    """
    Create raw IPv4 socket.

    Args:
        sndbuf: Size of buffer's socket

    Returns:
        A socket ready for sending.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sndbuf)
    return s
