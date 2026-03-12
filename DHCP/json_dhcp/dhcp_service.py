import socket
import json
import random

class DHCPService:
    def __init__(self):
        self.xid = random.randint(1000, 9999)
        self.port_server = 6767 # Matches Port_In in dhcp_protocol.py
        self.port_client = 6868 # Matches Port_Out in dhcp_protocol.py

    def get_ip_and_dns(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5.0)
            sock.bind(('', self.port_client))

            # DISCOVER
            discover = {"message_type": "DISCOVER", "transaction_id": self.xid}
            sock.sendto(json.dumps(discover).encode(), ('255.255.255.255', self.port_server))

            try:
                # OFFER
                data, _ = sock.recvfrom(1024)
                offer = json.loads(data.decode())
                offered_ip = offer.get("ip_address")

                # REQUEST
                request = {
                    "message_type": "REQUEST",
                    "transaction_id": self.xid,
                    "requested_ip": offered_ip
                }
                sock.sendto(json.dumps(request).encode(), ('255.255.255.255', self.port_server))

                # ACK
                data, _ = sock.recvfrom(1024)
                ack = json.loads(data.decode())
                return ack.get("ip_address"), ack.get("dns_server")

            except (socket.timeout, json.JSONDecodeError):
                return None, None