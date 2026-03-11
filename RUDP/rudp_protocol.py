import struct
import json

"""
Custom RUDP Header
We made a very simple RUDP protocol, based on the Go-Back-N mechanism


1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Sequence Number (4)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Total Packets (4)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                        Payload Data (Variable)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
"""


class RUDPProtocol:
    HEADER_FORMAT = "!II"  # Sequence Number (4 bytes), Total Packets (4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    MAX_PACKET_SIZE = 1450

    @staticmethod
    def create_packet(seq_num, total_packets, data):
        header = struct.pack(RUDPProtocol.HEADER_FORMAT, seq_num, total_packets)
        return header + data

    @staticmethod
    def parse_packet(packet_bytes):
        header = packet_bytes[:RUDPProtocol.HEADER_SIZE]
        data = packet_bytes[RUDPProtocol.HEADER_SIZE:]
        seq_num, total_packets = struct.unpack(RUDPProtocol.HEADER_FORMAT, header)
        return seq_num, total_packets, data

    @staticmethod
    def create_ack(seq_num):
        return json.dumps({"type": "ACK", "num": seq_num}).encode('utf-8')