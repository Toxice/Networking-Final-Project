import json
import socket

Broadcast_In = "255.255.255.255"
Broadcast_Out = "0.0.0.0"
Port_In = 6767
Port_Out = 6868


class DHCPServer:
    def __init__(self, ip_mask: str, allocation: int, dns):
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
        self.transaction_id = None
        self.dns_server = dns

    def __generate_pool(self):
        return [f"{self.ip_mask}.{i}" for i in range(1, self.alloc + 1)]

    def serve(self):
        self.server.bind((Broadcast_Out, Port_In))
        print(f"[DHCP] Listening on Port {Port_In}...")
        while True:
            data, address = self.server.recvfrom(1024)
            print(f"[DHCP] Got a DHCP Request")

            request = json.loads(data.decode(encoding="utf-8"))

            # Updated to match FTPClient.py keys
            match request.get("message_type"):
                case "DISCOVER":
                    self.handle_discover(request.get("transaction_id"))
                case "REQUEST":
                    self.handle_request(request.get("transaction_id"), request.get("requested_ip"))

    def dhcp_offer(self, transaction_id: int):
        """
        Creates the OFFER message (does NOT remove the IP from the pool yet).
        :param transaction_id: Transaction ID
        :return: OFFER message as bytes
        """
        # Updated to match FTPClient.py keys
        payload = {
            "message_type": "OFFER",
            "transaction_id": transaction_id,
            "ip_address": self.ip_pool[0],
            "dns_server": self.dns_server
        }
        return json.dumps(payload).encode(encoding="utf-8")

    def dhcp_ack(self, transaction_id: int, ip_address):
        """
        Creates the ACK message and removes the IP from the pool.
        :param ip_address: the IP address was allocated by the server earlier
        :param transaction_id: Transaction ID
        :return: ACK message as bytes
        """
        if ip_address == self.ip_pool[0]:
            # Updated to match FTPClient.py keys
            payload = {
                "message_type": "ACK",
                "transaction_id": transaction_id,
                "ip_address": self.ip_pool.pop(0),
                "dns_server": self.dns_server
            }
            return json.dumps(payload).encode(encoding="utf-8")
        else:
            # Fixed raw dict return to JSON string
            payload = {
                "message_type": "NACK",
                "transaction_id": transaction_id
            }
            return json.dumps(payload).encode(encoding="utf-8")

    def handle_discover(self, transaction_id: int):
        if not self.ip_pool:
            print("[DHCP] No IPs available, ignoring DISCOVER.")
            return
        response = self.dhcp_offer(transaction_id)
        print(f"[DHCP] received DISCOVER on id: {transaction_id}")
        self.server.sendto(response, (Broadcast_In, Port_Out))

    def handle_request(self, transaction_id: int, ip_address):
        if not self.ip_pool:
            print("[DHCP] No IPs available, ignoring REQUEST.")
            return
        response = self.dhcp_ack(transaction_id, ip_address)
        print(f"[DHCP] received REQUEST on id {transaction_id}")
        self.server.sendto(response, (Broadcast_In, Port_Out))