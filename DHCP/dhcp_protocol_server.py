import json
import socket

Broadcast_In = "255.255.255.255"
Broadcast_Out = "0.0.0.0"
Port_In = 67
Port_Out = 68

class DHCPServer:
    def __init__(self, lease_time: int, ip_mask: str, allocation: int):
        """
        DHCP Constructor
        :param lease_time: lease time, in seconds
        :param ip_mask: 3 part string of ip, 24bit (like "192.168.10")
        :param allocation: number of IPs to allocate (2–256, defaults to 10 if out of range)
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.lease_time = lease_time
        self.alloc = allocation if (2 <= allocation <= 10) else 10
        self.ip_mask = ip_mask
        self.ip_pool = self.__generate_pool()

    def __generate_pool(self):
        return [f"{self.ip_mask}.{i}" for i in range(1, self.alloc + 1)]

    def serve(self):
        self.server.bind(("", Port_In))  # fix: socket must be bound before recvfrom
        print(f"[DHCP] Listening on Port {Port_In}...")
        while True:
            data, address = self.server.recvfrom(1024)
            print(f"[DHCP] Got a request from {address}")

            request = json.loads(data.decode(encoding="utf-8"))
            match request.get("type"):
                case "DISCOVER":
                    self.handle_offer(request.get("id"))
                case "REQUEST":
                    self.handle_ack(request.get("id"))

    def dhcp_offer(self, message_id: int):
        """
        Creates the OFFER message (does NOT remove the IP from the pool yet).
        :param message_id: Transaction ID
        :return: OFFER message as bytes
        """
        payload = {
            "type": "OFFER",
            "id": message_id,
            "ip": self.ip_pool[0],
            "lease_time": self.lease_time,
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def dhcp_ack(self, message_id: int):
        """
        Creates the ACK message and removes the leased IP from the pool.
        :param message_id: Transaction ID
        :return: ACK message as bytes
        """
        payload = {
            "type": "ACK",
            "id": message_id,
            "ip": self.ip_pool.pop(0),
            "lease_time": self.lease_time,
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def handle_offer(self, transaction_id: int):
        if not self.ip_pool:
            print("[DHCP] No IPs available, ignoring DISCOVER.")
            return
        response = self.dhcp_offer(transaction_id)
        self.server.sendto(response, (Broadcast_In, Port_Out))  # fix: sendto needs a (host, port) tuple

    def handle_ack(self, transaction_id: int):
        if not self.ip_pool:
            print("[DHCP] No IPs available, ignoring REQUEST.")
            return
        response = self.dhcp_ack(transaction_id)
        self.server.sendto(response, (Broadcast_In, Port_Out))  # fix: same tuple fix


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
