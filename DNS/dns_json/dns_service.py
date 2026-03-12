import socket
import json


class DNSService:
    def __init__(self, dns_server_ip):
        self.dns_server_ip = dns_server_ip
        self.port = 8053

    def resolve(self, hostname):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3.0)
            query = json.dumps({"url": hostname})

            try:
                sock.sendto(query.encode(), (self.dns_server_ip, self.port))
                data, _ = sock.recvfrom(1024)
                response = json.loads(data.decode())
                return response.get("ip")
            except Exception:
                return None