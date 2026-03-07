# dhcp_model.py

from dataclasses import dataclass, field
from typing import List, Dict

"""
as mentioned at https://www.ietf.org/rfc/rfc2131.txt:

       0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |     op (1)    |   htype (1)   |   hlen (1)    |   hops (1)    |
      +---------------+---------------+---------------+---------------+
      |                            xid (4)                            |
      +-------------------------------+-------------------------------+
      |           secs (2)            |           flags (2)           |
      +-------------------------------+-------------------------------+
      |                          ciaddr  (4)                          |
      +---------------------------------------------------------------+
      |                          yiaddr  (4)                          |
      +---------------------------------------------------------------+
      |                          siaddr  (4)                          |
      +---------------------------------------------------------------+
      |                          giaddr  (4)                          |
      +---------------------------------------------------------------+
      |                                                               |
      |                          chaddr  (16)                         |
      |                                                               |
      |                                                               |
      +---------------------------------------------------------------+
      |                                                               |
      |                          sname   (64)                         |
      +---------------------------------------------------------------+
      |                                                               |
      |                          file    (128)                        |
      +---------------------------------------------------------------+
      |                                                               |
      |                          options (variable)                   |
      +---------------------------------------------------------------+

"""

# Hardcoded ports for this custom implementation
SERVER_PORT = 6767
CLIENT_PORT = 6868

@dataclass
class DHCPPacket:
    op: int = 1               # 1 for Request (Client->Server), 2 for Reply (Server->Client)
    htype: int = 1            # Ethernet
    hlen: int = 6             # MAC length
    hops: int = 0
    xid: int = 0              # Transaction ID (must match across DORA)
    secs: int = 0             # Lease Time | a time in seconds a client can hold an IP address
    flags: int = 0x8000       # Broadcast flag (often required for clients without IPs)
    ciaddr: str = "0.0.0.0"   # Client IP address | Redundant in Our Case
    yiaddr: str = "0.0.0.0"   # Your IP Address | Client IP Address
    siaddr: str = "0.0.0.0"   # Server IP Address
    giaddr: str = "0.0.0.0"
    chaddr: bytes = b''       # Binary MAC address
    options: Dict[int, bytes] = field(default_factory=dict)