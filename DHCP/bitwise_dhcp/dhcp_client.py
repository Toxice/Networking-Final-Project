import socket
import uuid
import random
import dhcp_protocol
from dhcp_model import SERVER_PORT, CLIENT_PORT


class DHCPClient:
    def __init__(self):
        # Generate a unique Transaction ID (xid) for this session
        self.xid = random.randint(0, 0xFFFFFFFF)
        self.mac_addr = self._get_mac_binary()

    def _get_mac_binary(self) -> bytes:
        """Extracts the local hardware MAC address as 6 bytes."""
        node = uuid.getnode()
        return node.to_bytes(6, 'big')

    def run_dora(self):
        """Executes the DORA exchange using dhcp_protocol factory methods."""

        # Initialize UDP socket for broadcast-style communication
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5.0)

            # Bind to the standardized client port
            sock.bind(('', CLIENT_PORT))
            # server_addr = ('<broadcast>, SERVER_PORT)
            server_addr = ('127.0.0.1', SERVER_PORT)

            try:
                # --- 1. DISCOVER ---
                # Uses dhcp_protocol.create_discover
                print(f"[*] Discovering servers with xid: {hex(self.xid)}...")
                discover_data = dhcp_protocol.create_discover(self.xid, self.mac_addr)
                sock.sendto(discover_data, server_addr)

                # --- 2. OFFER ---
                # Uses dhcp_protocol.unpack_dhcp_packet
                data, _ = sock.recvfrom(1024)
                offer_pkt = dhcp_protocol.unpack_dhcp_packet(data)

                if offer_pkt.xid != self.xid:
                    print("[-] Transaction ID mismatch. Ignoring packet.")
                    return

                print(f"[+] Received OFFER: {offer_pkt.yiaddr} from {offer_pkt.siaddr}")

                # --- 3. REQUEST ---
                # Uses dhcp_protocol.create_request
                print(f"[*] Requesting IP: {offer_pkt.yiaddr}...")
                request_data = dhcp_protocol.create_request(
                    self.xid, self.mac_addr, offer_pkt.yiaddr, offer_pkt.siaddr
                )
                sock.sendto(request_data, server_addr)

                # --- 4. ACK ---
                # Uses dhcp_protocol.unpack_dhcp_packet
                data, _ = sock.recvfrom(1024)
                ack_pkt = dhcp_protocol.unpack_dhcp_packet(data)

                if ack_pkt.options.get(53) == b'\x05':
                    print(f"[SUCCESS] Leased IP: {ack_pkt.yiaddr}")
                    print(f"Server Identifier: {ack_pkt.siaddr}")
                else:
                    print("[-] DHCP NAK received or invalid response.")

            except socket.timeout:
                print("[-] Error: No response from DHCP server (Timeout).")


if __name__ == "__main__":
    client = DHCPClient()
    client.run_dora()