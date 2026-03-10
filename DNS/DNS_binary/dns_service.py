import socket
import struct
import random

class DNSService:
    DNS_SERVER_PORT = 8053
    BUFFER_SIZE = 65535
    TIMEOUT = 5

    def __init__(self, dns_server_ip):
        self.dns_server_ip = dns_server_ip

    def resolve(self, hostname):
        if not self.dns_server_ip:
            return None

        print(f"--- Resolving {hostname} ---")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self.TIMEOUT)
            transaction_id = 0x1234
            query = self._build_query(hostname, transaction_id)

            try:
                sock.sendto(query, (self.dns_server_ip, self.DNS_SERVER_PORT))
                data, _ = sock.recvfrom(self.BUFFER_SIZE)
                if len(data) >= 16:
                    return socket.inet_ntoa(data[-4:])
            except Exception as e:
                print(f"DNS Resolution failed: {e}")
        return None

    def _build_query(self, hostname, tx_id):
        header = struct.pack("!HHHHHH", tx_id, 0x0100, 1, 0, 0, 0)
        question = b''
        for part in hostname.split('.'):
            question += struct.pack("!B", len(part)) + part.encode()
        question += b'\x00' + struct.pack("!HH", 1, 1)
        return header + question