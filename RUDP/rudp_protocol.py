import struct

"""
Custom RUDP Header (12-Byte Aligned)
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Sequence Number (4)                     |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Total Packets (4)                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |   Flags (1)   |                 Padding (3)                   |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""

class RUDPProtocol:
    """
    ! = Network (Big-Endian)
    I = Unsigned Int (4B)
    B = Unsigned Char (1B)
    3x = 3 Pad Bytes
    """
    HEADER_FORMAT = "!IIB3x"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    MAX_PAYLOAD_SIZE = 1450

    # Bitmask Flags
    DATA_FLAG = 0x00
    FIN_FLAG  = 0x01
    ACK_FLAG  = 0x02
    SYN_FLAG  = 0x04

    @staticmethod
    def create_packet(seq_num, total_packets, data, flags=0x00):
        header = struct.pack(RUDPProtocol.HEADER_FORMAT, seq_num, total_packets, flags)
        return header + data

    @staticmethod
    def parse_packet(packet_bytes):
        if len(packet_bytes) < RUDPProtocol.HEADER_SIZE:
            return None
        header = packet_bytes[:RUDPProtocol.HEADER_SIZE]
        data = packet_bytes[RUDPProtocol.HEADER_SIZE:]
        seq_num, total_packets, flags = struct.unpack(RUDPProtocol.HEADER_FORMAT, header)
        return seq_num, total_packets, flags, data

    @staticmethod
    def create_ack(seq_num):
        # ACKs carry no payload and have the ACK_FLAG set
        return RUDPProtocol.create_packet(seq_num, 0, b"", flags=RUDPProtocol.ACK_FLAG)