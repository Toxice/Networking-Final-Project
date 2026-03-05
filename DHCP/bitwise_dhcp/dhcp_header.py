# dhcp_header.py

import struct
from dataclasses import dataclass

@dataclass
class DHCPHeader:
    # DHCP Header Fields
    op: int = 1 # Operation Code | Default to 1
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




