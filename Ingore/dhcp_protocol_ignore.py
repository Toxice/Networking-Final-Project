import json
import socket

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
        self.alloc = allocation if (2 < allocation < 10) else 10
        self.ip_mask = ip_mask
        self.ip_pool = self.__generate_pool()

    def __generate_pool(self):
        ip_pool:list = []
        for pool in range(self.alloc):
            lease_ip = f"{self.ip_mask}.{pool}"
            ip_pool.append(lease_ip)
        return ip_pool

    def serve(self):
        print(f"[DHCP] Listening on Port {Port_In}...")
        while True:
            data, address = self.server.recvfrom(1024)
            print(f"[DHCP] got a request on {address}")

            request = json.loads(data.decode(encoding="utf-8"))
            match request.get("type"):
                case "DISCOVER":
                    self.handle_offer(request.get("id"))
                case "REQUEST":
                    self.handle_ack(request.get("id"))


    def dhcp_offer(self, message_id: int):
        """
        creates the OFFER message
        :param message_id: Transaction ID
        :return: OFFER message
        """
        payload = {"type": "OFFER",
                   "id": message_id,
                   "ip": self.ip_pool[0]}
        return (json.dumps(payload) + "/").encode(encoding="utf-8")

    def dhcp_ack(self, message_id):
        """
        create the ACK message
        :param message_id: Transaction ID
        :return: ACK message
        """
        payload = {"type": "ACK",
                   "id": message_id,
                     "ip": self.ip_pool.pop(0)}
        return (json.dumps(payload) + "/").encode(encoding="utf-8")

    def handle_offer(self, transaction_id):
        response = self.dhcp_offer(transaction_id)
        self.server.sendto(response, Broadcast_In)

    def handle_ack(self, transaction_id):
        response = self.dhcp_ack(transaction_id)
        self.server.sendto(response, Broadcast_In)

'''
the DHCP Client is redundant for now, Liz will implement it on the Project's Client

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
'''