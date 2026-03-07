# dhcp_server.py

import socket
import argparse
from dhcp_model import DHCPPacket
import dhcp_protocol


class DHCPServer:
    def __init__(self, ip_pool, subnet_mask):
        self.ip_pool = ip_pool  # List of available IPs
        self.subnet_mask = subnet_mask
        self.leases = {}  # MAC -> IP mapping

    def handle_discover(self, request_packet):
        print(f"[*] Received DISCOVER from {request_packet.chaddr.hex(':')}")
        # Logic: Pick an IP from pool, create OFFER packet
        # ...
        pass

    def handle_request(self, request_packet):
        print(f"[*] Received REQUEST for {request_packet.yiaddr}")
        # Logic: Confirm lease, create ACK packet
        # ...
        pass

    def serve(self, interface_ip):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', 67))

        print(f"Listening on port 67...")
        while True:
            data, addr = sock.recvfrom(1024)
            # Basic logic to parse 'data' into DHCPPacket and route to handlers
            # ...


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python DHCP Server")
    parser.add_argument("--pool", nargs='+', required=True, help="IP pool range")
    parser.add_argument("--mask", default="255.255.255.0", help="Subnet mask")
    args = parser.parse_args()

    server = DHCPServer(args.pool, args.mask)
    server.serve("0.0.0.0")