import socket
import argparse
import dhcp_protocol
import sys

from dhcp_model import SERVER_PORT, CLIENT_PORT

class DHCPServer:
    def __init__(self, server_ip, interface, subnet_mask="255.255.255.0"):
        self.server_ip = server_ip
        self.interface = interface
        self.subnet = subnet_mask
        prefix = ".".join(server_ip.split('.')[:-1])
        self.ip_pool = [f"{prefix}.{i}" for i in range(100, 201)]

    def handle_packet(self, data):
        pkt = dhcp_protocol.unpack_dhcp_packet(data)
        msg_type = pkt.options.get(53)

        if msg_type == b'\x01':  # DISCOVER
            offered_ip = self.ip_pool[0]
            return dhcp_protocol.create_offer(pkt.xid, pkt.chaddr, offered_ip, self.server_ip)

        elif msg_type == b'\x03':  # REQUEST
            req_ip = socket.inet_ntoa(pkt.options.get(50, b'\x00\x00\x00\x00'))
            return dhcp_protocol.create_ack(pkt.xid, pkt.chaddr, req_ip, self.server_ip)
        return None

    def serve(self, port=SERVER_PORT):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # --- CROSS-PLATFORM INTERFACE LOGIC ---
        if sys.platform.startswith('linux'):
            try:
                # Linux approach: Bind directly to the hardware name
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.interface.encode())
                print(f"Linux: Bound to interface {self.interface}")
            except PermissionError:
                print("Permission denied: DHCP servers require sudo on Linux.")

        elif sys.platform == 'win32':
            # Windows approach: Bind to the IP address associated with the interface
            # On Windows, we bind to the specific local IP to lock the interface
            try:
                # sock.bind((self.server_ip, port))
                sock.bind(('127.0.0.1', port))
                print(f"Windows: Bound to IP {self.server_ip} on interface {self.interface}")
            except Exception as e:
                print(f"Windows Bind Error: {e}")
                sock.bind(('', port))  # Fallback to all interfaces

        # Final fallback/default bind for non-Windows or if Linux binding failed
        if sys.platform != 'win32':
            sock.bind(('', port))

        print(f"DHCP Server active. Serving pool: {self.ip_pool[0]}-{self.ip_pool[-1]}")
        while True:
            data, addr = sock.recvfrom(1024)
            response = self.handle_packet(data)
            if response:
                # sock.sendto(response, ('<broadcast>', CLIENT_PORT))
                sock.sendto(response, ('127.0.0.1', CLIENT_PORT))


if __name__ == "__main__":
    if __name__ == "__main__":
        def get_local_ip():
            """Automatically detect the IP of the default interface."""
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Doesn't actually connect, just triggers the OS to pick an interface
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
            except Exception:
                return "192.168.1.1"  # Total fallback
            finally:
                s.close()


        parser = argparse.ArgumentParser(description="DHCP Server")
        # If the user doesn't provide --ip, get_local_ip() runs automatically
        parser.add_argument("--ip", default=get_local_ip(), help="The Base IP for the server")
        parser.add_argument("--interface", default="eth0", help="Interface name")

        args = parser.parse_args()
        print(f"Using Base IP: {args.ip}")  # Confirms what was chosen
        server = DHCPServer(args.ip, args.interface)
        server.serve()