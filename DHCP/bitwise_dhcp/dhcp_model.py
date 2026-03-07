# dhcp_model.py

from dataclasses import dataclass, field
from typing import List, Dict

"""
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

@dataclass
class DHCPPacket:
    op: int = 1              # Operation Code | (1 for a REQUEST, 2 for a REPLY)
    htype: int = 1           # Hardware address type |Default as 1 for Ethernet
    hlen: int = 6            # Hardware address length | Default as 6 for MAC
    hops: int = 0            # Number of Hops | Similar to how the IP protocol counts the number of hops from router to router
    xid: int = 0             # Transaction ID | random number generated for maintaining the session
    secs: int = 0            # Lease Time | number of seconds a client can hold an address
    flags: int = 0           # Broadcast flag | Broadcast as 1, Unicast as 0
    ciaddr: str = "0.0.0.0"  # Client IP
    yiaddr: str = "0.0.0.0"  # 'Your' (client) IP
    siaddr: str = "0.0.0.0"  # Next server IP
    giaddr: str = "0.0.0.0"  # Relay agent IP
    chaddr: str = ""         # Client hardware address (MAC)
    options: Dict[int, bytes] = field(default_factory=dict)