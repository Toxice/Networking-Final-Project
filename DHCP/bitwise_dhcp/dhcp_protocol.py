import struct
import socket
from dhcp_model import DHCPPacket

MAGIC_COOKIE = b'\x63\x82\x53\x63'

def pack_dhcp_packet(packet: DHCPPacket) -> bytes:
    header = struct.pack(
        '!BBBBIHH4s4s4s4s16s',
        packet.op, packet.htype, packet.hlen, packet.hops,
        packet.xid, packet.secs, packet.flags,
        socket.inet_aton(packet.ciaddr), socket.inet_aton(packet.yiaddr),
        socket.inet_aton(packet.siaddr), socket.inet_aton(packet.giaddr),
        packet.chaddr.ljust(16, b'\x00')
    )
    # 192 bytes of padding (sname + file) + Magic Cookie
    body = header + (b'\x00' * 192) + MAGIC_COOKIE
    for code, val in packet.options.items():
        body += struct.pack('!BB', code, len(val)) + val
    return body + b'\xff'

def unpack_dhcp_packet(data: bytes) -> DHCPPacket:
    # Basic header unpacking (first 44 bytes)
    parts = struct.unpack('!BBBBIHH4s4s4s4s16s', data[:44])
    pkt = DHCPPacket(
        op=parts[0], xid=parts[4],
        ciaddr=socket.inet_ntoa(parts[7]), yiaddr=socket.inet_ntoa(parts[8]),
        siaddr=socket.inet_ntoa(parts[9]), giaddr=socket.inet_ntoa(parts[10]),
        chaddr=parts[11][:parts[2]]
    )
    # Simple option parser
    offset = 240 # Header(236) + Cookie(4)
    while offset < len(data):
        opt_type = data[offset]
        if opt_type == 255: break
        length = data[offset+1]
        pkt.options[opt_type] = data[offset+2 : offset+2+length]
        offset += 2 + length
    return pkt

# Factory functions for DORA

def create_discover(xid, mac_bin):
    p = DHCPPacket(xid=xid, chaddr=mac_bin); p.options[53] = b'\x01'
    return pack_dhcp_packet(p)

def create_offer(xid, mac_bin, yiaddr, siaddr):
    p = DHCPPacket(op=2, xid=xid, chaddr=mac_bin, yiaddr=yiaddr, siaddr=siaddr)
    p.options[53] = b'\x02'; p.options[54] = socket.inet_aton(siaddr)
    return pack_dhcp_packet(p)

def create_request(xid, mac_bin, requested_ip, siaddr):
    p = DHCPPacket(xid=xid, chaddr=mac_bin); p.options[53] = b'\x03'
    p.options[50] = socket.inet_aton(requested_ip); p.options[54] = socket.inet_aton(siaddr)
    return pack_dhcp_packet(p)

def create_ack(xid, mac_bin, yiaddr, siaddr):
    p = DHCPPacket(op=2, xid=xid, chaddr=mac_bin, yiaddr=yiaddr, siaddr=siaddr)
    p.options[53] = b'\x05'; p.options[54] = socket.inet_aton(siaddr)
    return pack_dhcp_packet(p)