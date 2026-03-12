import socket
import uuid
import random
from dhcp_bitwise import dhcp_protocol
from dhcp_bitwise.dhcp_model import SERVER_PORT, CLIENT_PORT, DHCPState


class DHCPService:
    def __init__(self):
        self.xid = random.randint(0, 0xFFFFFFFF)
        self.mac_addr = self._get_mac_binary()

    @staticmethod
    def _get_mac_binary() -> bytes:
        node = uuid.getnode()
        return node.to_bytes(6, 'big')

    def get_ip_and_dns(self):
        """Executes DORA and returns (assigned_ip, dns_server)"""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5.0)

            sock.bind(('', CLIENT_PORT))
            server_addr = ('127.0.0.1', SERVER_PORT)  # Localhost for testing

            try:
                # DISCOVER
                discover_data = dhcp_protocol.create_discover(self.xid, self.mac_addr)
                sock.sendto(discover_data, server_addr)

                # OFFER
                data, _ = sock.recvfrom(1024)
                offer_pkt = dhcp_protocol.unpack_dhcp_packet(data)

                # REQUEST
                request_data = dhcp_protocol.create_request(
                    self.xid, self.mac_addr, offer_pkt.yiaddr, offer_pkt.siaddr
                )
                sock.sendto(request_data, server_addr)

                # ACK
                data, _ = sock.recvfrom(1024)
                ack_pkt = dhcp_protocol.unpack_dhcp_packet(data)

                if ack_pkt.options.get(53) == DHCPState.ACK:
                    dns_bytes = ack_pkt.options.get(6)
                    dns_str = socket.inet_ntoa(dns_bytes) if dns_bytes else None
                    return ack_pkt.yiaddr, dns_str

            except socket.timeout:
                print("[-] DHCP Timeout.")
            return None, None