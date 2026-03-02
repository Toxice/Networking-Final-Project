import json
import socket
import threading

Broadcast_In = "255.255.255.255"
Broadcast_Out = "0.0.0.0"
Port_In = 67
Port_Out = 68
DNS = "127.0.0.1"

class DHCPServer:
    def __init__(self,ip_mask: str, allocation: int):
        """
        DHCP Constructor
        :param ip_mask: 3 part string of ip, 24bit (like "192.168.10")
        :param allocation: number of IPs to allocate (2–256, defaults to 10 if out of range)
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.alloc = allocation if (2 <= allocation <= 10) else 10
        self.ip_mask = ip_mask
        self.ip_pool = self.__generate_pool()

    def __generate_pool(self):
        return [f"{self.ip_mask}.{i}" for i in range(1, self.alloc + 1)]

    def serve(self):
        self.server.bind(("", Port_In))
        print(f"[DHCP] Listening on Port {Port_In}...")
        while True:
            data, address = self.server.recvfrom(1024)
            print(f"[DHCP] Got a DHCP Request")

            request = json.loads(data.decode(encoding="utf-8"))
            match request.get("type"):
                case "DISCOVER":
                    threading.Thread(target=self.handle_discover, args=(request.get("id"))).start()
                case "REQUEST":
                    threading.Thread(target=self.handle_request, args=(request.get("id"))).start()

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
            "dns": DNS
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def dhcp_ack(self, message_id: int):
        """
        Creates the ACK message and removes the IP from the pool.
        :param message_id: Transaction ID
        :return: ACK message as bytes
        """
        payload = {
            "type": "ACK",
            "id": message_id,
            "ip": self.ip_pool.pop(0),
            "dns": DNS
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def handle_discover(self, transaction_id: int):
        if not self.ip_pool:
            print("[DHCP] No IPs available, ignoring DISCOVER.")
            return
        response = self.dhcp_offer(transaction_id)
        print(f"[DHCP] received DISCOVER on id: {transaction_id}")
        self.server.sendto(response, (Broadcast_In, Port_Out))

    def handle_request(self, transaction_id: int):
        if not self.ip_pool:
            print("[DHCP] No IPs available, ignoring REQUEST.")
            return
        response = self.dhcp_ack(transaction_id)
        print(f"[DHCP] received REQUEST on id {transaction_id}")
        self.server.sendto(response, (Broadcast_In, Port_Out))
