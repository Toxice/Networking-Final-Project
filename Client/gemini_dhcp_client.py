import json
import socket
import random

Broadcast_In = "255.255.255.255"
Broadcast_Out = "0.0.0.0"
Port_In = 67
Port_Out = 68


class DHCPClient:
    def __init__(self):
        self.random = random
        self.session_id = self.generate_session_id()
        self.client = None
        self.assigned_ip = None

    def generate_session_id(self) -> int:
        return self.random.randint(1000, 9999)

    def init_client(self):
        # Fix socket instantiation and add binding so it can receive the server's replies
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Bind to Port_Out (68) to listen for the server's broadcasts
        self.client.bind((Broadcast_Out, Port_Out))

    def dhcp_discover(self) -> bytes:
        # Match the "type" key the server expects and encode to bytes
        payload = {
            "type": "DISCOVER",
            "id": self.session_id
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def dhcp_request(self) -> bytes:
        payload = {
            "type": "REQUEST",
            "id": self.session_id
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def run(self) -> str:
        """Executes the D.O.R.A state machine"""
        self.init_client()

        # 1. DISCOVER
        print("[Client] Sending DISCOVER...")
        self.client.sendto(self.dhcp_discover(), (Broadcast_In, Port_In))

        # 2. OFFER
        while True:
            data, addr = self.client.recvfrom(1024)
            response = json.loads(data.decode("utf-8"))

            if response.get("type") == "OFFER" and response.get("id") == self.session_id:
                offered_ip = response.get("ip")
                print(f"[Client] Received OFFER for IP: {offered_ip}")
                break

        # 3. REQUEST
        print("[Client] Sending REQUEST...")
        self.client.sendto(self.dhcp_request(), (Broadcast_In, Port_In))

        # 4. ACK
        while True:
            data, addr = self.client.recvfrom(1024)
            response = json.loads(data.decode("utf-8"))

            if response.get("type") == "ACK" and response.get("id") == self.session_id:
                self.assigned_ip = response.get("ip")
                print(
                    f"[Client] Received ACK. Successfully leased IP: {self.assigned_ip} for {response.get('lease_time')}s")
                break