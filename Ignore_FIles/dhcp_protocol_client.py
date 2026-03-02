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
        self.client = socket.socket

    def generate_session_id(self) -> int:
        """
        function responsible for generating a random ID for the session between the DHCP client and the DHCP server
        :return: random session ID
        """
        return self.random.randint(1000, 9999)

    def dhcp_discover(self):
        return {"command": "DISCOVER",
                "id": self.session_id}

    def handle_discover(self, session_id: int):
        pass

    def dhcp_request(self, session_id:int, ip:str):
        pass

    def handle_request(self):
        pass

    def init_client(self):
        self.client(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST)

'''
The DHCP Client is redundant for now, Liz will implement it on the Project's Client.

class DHCPClient:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.transaction_id = self.__generate_transaction_id()
        self.client.sendto(self.dhcp_discover(), (Broadcast_Out, Port_Out))

    @staticmethod
    def __generate_transaction_id() -> int:
        return random.randint(1000, 9999)

    def dhcp_discover(self) -> bytes:
        payload = {"type": "DISCOVER",
                   "id": self.transaction_id}
        return json.dumps(payload).encode(encoding="utf-8")

    def dhcp_request(self):
        pass
'''
