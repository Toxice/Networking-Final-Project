import struct
import json


class RUDPProtocol:
    HEADER_FORMAT = "!II"  # Sequence Number (4 bytes), Total Packets (4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    MAX_PACKET_SIZE = 30000

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