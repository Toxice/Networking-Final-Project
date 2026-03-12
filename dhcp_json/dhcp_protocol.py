import json
import socket


class DHCPServer:
    def __init__(self, ip_mask="10.100.102", allocation=10, dns=None):
        self.ip_mask = ip_mask
        self.allocation = max(2, min(allocation, 254))  # Clamp between 2 and 254
        self.dns_server = dns or self._load_dns_from_file()
        self.port = 6767

        # IP Pool Management
        # We'll start allocating from .10 up to .10 + allocation
        self.start_ip = 10
        self.pool = {}  # Dictionary to track {transaction_id: assigned_ip}

    def _load_dns_from_file(self):
        try:
            with open("dhcp.json", "r") as f:
                data = json.load(f)
                return data.get("dns_server", "10.100.102.5")
        except (FileNotFoundError, json.JSONDecodeError):
            return "10.100.102.5"

    def _get_next_available_ip(self, xid):
        """
        Simple pool logic: find the next free index in our allocation range.
        """
        # If this transaction ID already has an assignment, return it
        if xid in self.pool:
            return self.pool[xid]

        # Otherwise, find a new one
        for i in range(self.start_ip, self.start_ip + self.allocation):
            potential_ip = f"{self.ip_mask}.{i}"
            if potential_ip not in self.pool.values():
                self.pool[xid] = potential_ip
                return potential_ip

        return None  # Pool exhausted

    def handle(self, raw_data):
        if not raw_data:
            return b''
        try:
            data = json.loads(raw_data.decode("utf8"))
            msg_type = data.get("message_type")
            xid = data.get("transaction_id")

            print(f"[DHCP RECEIVE] {msg_type} | ID: {xid}")

            # Allocate or retrieve IP from the pool
            assigned_ip = self._get_next_available_ip(xid)
            if not assigned_ip:
                print(f"[DHCP ERROR] Pool exhausted! Cannot serve ID: {xid}")
                return json.dumps({"error": "No IPs available"}).encode("utf8")

            out_type = "OFFER" if msg_type == "DISCOVER" else "ACK"

            response = {
                "message_type": out_type,
                "transaction_id": xid,
                "ip_address": assigned_ip,
                "dns_server": self.dns_server
            }

            final_json = json.dumps(response)
            print(f"[DHCP SEND] {out_type} | Assigned: {assigned_ip} | DNS: {self.dns_server}")
            return final_json.encode("utf8")

        except Exception as e:
            print(f"[DHCP ERROR] {e}")
            return b''

    def serve(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            try:
                sock.bind(("0.0.0.0", self.port))
                print(f"\n[DHCP] DHCP Server Live | Port: {self.port}")
                #print(f"[DHCP] Pool: {self.ip_mask}.{self.start_ip} to .{self.start_ip + self.allocation - 1}")
                print(f"[DHCP] Pool: {self.ip_mask}.{self.start_ip} to {self.ip_mask}.{str(self.allocation - 1)}")
                print("-" * 50)
            except OSError as e:
                print(f"[DHCP] Bind Error: {e}")
                return

            while True:
                raw_data, addr = sock.recvfrom(1024)
                response = self.handle(raw_data)
                if response:
                    sock.sendto(response, addr)