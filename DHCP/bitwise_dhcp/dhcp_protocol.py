# dhcp_protocol.py

import struct
import socket
from dhcp_model import DHCPPacket

MAGIC_COOKIE = b'\x63\x82\x53\x63'


def ip_to_bytes(ip: str) -> bytes:
    return socket.inet_aton(ip)


def pack_packet(packet: DHCPPacket) -> bytes:
    # Format: ! (network) B B B B I H H 4s 4s 4s 4s 16s (total 44 bytes for header)
    # Note: chaddr is 16 bytes, but we usually only use 6 for Ethernet.
    header = struct.pack(
        '!BBBBIHH4s4s4s4s16s',
        packet.op, packet.htype, packet.hlen, packet.hops,
        packet.xid, packet.secs, packet.flags,
        ip_to_bytes(packet.ciaddr), ip_to_bytes(packet.yiaddr),
        ip_to_bytes(packet.siaddr), ip_to_bytes(packet.giaddr),
        packet.chaddr.ljust(16, b'\x00')
    )

    # Fill sname (64 bytes) and file (128 bytes) with zeros
    padding = b'\x00' * (64 + 128)

    # Options processing
    options_bin = MAGIC_COOKIE
    for opt_code, data in packet.options.items():
        options_bin += struct.pack('!BB', opt_code, len(data)) + data
    options_bin += b'\xff'  # End option

    return header + padding + options_bin