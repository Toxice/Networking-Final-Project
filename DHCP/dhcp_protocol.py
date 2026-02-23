import json

from ip import IP
import socket
import random

Broadcast_In = "255.255.255.255"
Broadcast_Out = "0.0.0.0"
Port_In = 67
Port_Out = 68

class DHCPServer:
    def __init__(self, lease_time:int, ip_mask:str, allocation:int):
        """
        DHCP Constructor
        :param lease_time: lease time, in seconds
        :param ip_mask: 3 part string of ip, 24bit (like "192.168.10")
        :param allocation: amount of ip's we can use, implementation is limited to up to 256,
         if we get less than 2 or more than 256, we get 256 as default
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.lease_time = lease_time
        self.alloc = allocation if (2 < allocation < 256) else 256
        self.ip_pool = self.__generate_pool()

    def __generate_pool(self):
        ip_pool:list[IP] = []
        for pool in range(self.alloc):
            lease_ip = f"{self.alloc}.{pool}"
            ip_pool.append(IP(lease_ip, self.lease_time, False))
        return ip_pool

    def serve(self):
        print(f"[DHCP] Listening on Port {Port_In}...")
        while True:
            data, address = self.server.recv(1024)
            print(f"[DHCP] got a request")

    def dhcp_offer(self):
        pass

    def dhcp_ack(self):
        pass

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
        return (json.dumps(payload) + "/").encode(encoding="utf-8")

    def dhcp_request(self):
        pass
