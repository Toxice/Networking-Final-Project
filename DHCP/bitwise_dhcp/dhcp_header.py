# dhcp_header.py

import struct
import secrets
from dataclasses import dataclass

'''
    we will use secrets.randbits(32) for xid
'''

@dataclass
class DHCPHeader:
    # DHCP Header Fields
    op: int = 1 # Operation Code | Default to 1 (1 - DISCOVER/REQUEST | 2 - OFFER/ACK)
    htype: int = 1 # Default at 1 for Ethernet
    hlen: int = 6 # Hardware Length | Default at 6 for MAC Address
    hops: int = 0 # Hop Count
    xid: int = 0 # transaction id
    secs: int = 86400 # lease time
    flags:int = 0x8000 # broadcast flag
    ciaddr:int = 0 # client IP address
    yiaddr:int = 0 # your IP address
    siaddr:int = 0 # server IP address
    giaddr:int = 0 # gateway IP address
    chaddr:bytes = b'\x00' * 16  # Must be 16 bytes
    sname:bytes = b'\x00' * 64   # Must be 64 bytes
    file:bytes = b'\x00' * 128  # Must be 128 bytes
    magic_cookie:int = 0x63825363 # a fixed value

    def pack(self, options: bytes) -> bytes:
        """Serializes the header and appends DHCP options."""
        # Format string:
        # ! (network/big-endian)
        # B (1 byte) x 4, L (4 bytes) x 1, H (2 bytes) x 2, L (4 bytes) x 4,
        # 16s (16 bytes), 64s (64 bytes), 128s (128 bytes), L (4 bytes)
        header_fmt = "!BBBBLHHLLLL16s64s128sL"

        header_bytes = struct.pack(
            header_fmt,
            self.op, self.htype, self.hlen, self.hops,
            self.xid, self.secs, self.flags,
            self.ciaddr, self.yiaddr, self.siaddr, self.giaddr,
            self.chaddr, self.sname, self.file,
            self.magic_cookie
        )
        return header_bytes + options + b'\xff'  # End option

    @staticmethod
    def create_option(code: int, value: bytes) -> bytes:
        """
        Enter Your Option Value to the option field
        :param code:
        :param value:
        :return:
        """
        return struct.pack("!BB", code, len(value)) + value

    def create_discover(self, xid: int, mac_address: bytes) -> bytes:
        """
        DHCPDISCOVER
        :param xid: transaction id
        :param mac_address: MAC Address
        :return: the new packed header
        """
        header = DHCPHeader(xid=xid, chaddr=mac_address.ljust(16, b'\x00'))
        # Option 53: 1 (Discover)
        options = self.create_option(53, b'\x01')
        return header.pack(options)

    def create_offer(self, xid: int, yiaddr: int, server_ip: int) -> bytes:
        """
        DHCPOFFER
        :param xid: transaction id
        :param yiaddr: you ip address
        :param server_ip: server ip address
        :return: the new packed header
        """
        header = DHCPHeader(op=2, xid=xid, yiaddr=yiaddr, siaddr=server_ip)
        # Option 53: 2 (Offer)
        options = self.create_option(53, b'\x02')
        return header.pack(options)

    def create_request(self, xid: int, requested_ip: int, mac_address: bytes) -> bytes:
        """
        DHCPREQUEST
        :param xid: transaction id
        :param requested_ip: requested ip
        :param mac_address: MAC Address
        :return: new packed header
        """
        header = DHCPHeader(xid=xid, chaddr=mac_address.ljust(16, b'\x00'))
        # Option 53: 3 (Request) | Option 50: Requested IP
        options = self.create_option(53, b'\x03') + \
                  self.create_option(50, struct.pack("!L", requested_ip))
        return header.pack(options)

    def create_ack(self, xid: int, yiaddr: int, lease_time: int) -> bytes:
        """
        DHCPACK
        :param xid: transaction id
        :param yiaddr: your ip address
        :param lease_time: lease time
        :return: new packed header
        """
        header = DHCPHeader(op=2, xid=xid, yiaddr=yiaddr)
        # Option 53: 5 (ACK) | Option 51: Lease Time
        options = self.create_option(53, b'\x05') + \
                  self.create_option(51, struct.pack("!L", lease_time))
        return header.pack(options)




