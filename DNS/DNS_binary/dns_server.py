import socket
import random
import time
import struct
import json
# Importing classes directly to help with clarity and circularity
from dns_protocol import ZoneDatabase, DNSResponseBuilder


# a class for working with raw socket
class UdpTransport:
    def __init__(self, host, port, timeout=2, buffer_size=1024, receive_loss_rate=0.0,
                 send_loss_rate=0.0, artificial_delay_ms=0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.receive_loss_rate = receive_loss_rate
        self.send_loss_rate = send_loss_rate
        self.artificial_delay_ms = artificial_delay_ms
        self.sock = None
        self.running = False

    def initialize(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(self.timeout)
        self.running = True
        print(f"[DNS] server running on {self.host}:{self.port}")

    def receive(self):
        try:
            data, addr = self.sock.recvfrom(self.buffer_size)
            if random.random() < self.receive_loss_rate:
                print("Dropped incoming packet")
                return None, None
            if self.artificial_delay_ms > 0:
                time.sleep(self.artificial_delay_ms / 1000)
            return data, addr
        except socket.timeout:
            return None, None
        except Exception as e:
            print(f"Receive error: {e}")
            return None, None

    def send(self, data, addr):
        if not data:
            return

        if random.random() < self.send_loss_rate:
            print("Dropped outgoing packet")
            return
        if self.artificial_delay_ms > 0:
            time.sleep(self.artificial_delay_ms / 1000)
        try:
            self.sock.sendto(data, addr)
            print("[DNS] sent response")
        except Exception as e:
            print(f"Send error: {e}")

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()


class DNSServer:
    def __init__(self, zone_database):
        self.zone_database = zone_database
        # Fix: Ensure the database has the 'zones' attribute initialized
        if not hasattr(self.zone_database, 'zones'):
            self.zone_database.zones = []
            # Populate zones from the keys in the loaded database
            for key in self.zone_database.database.keys():
                z = self.zone_database.extract_zone(key)
                if z not in self.zone_database.zones:
                    self.zone_database.zones.append(z)

    def handle_request(self, data):
        # Basic DNS header validation
        if data is None or len(data) < 12:
            return b''

        try:
            # We use the builder to parse the incoming binary request
            builder = DNSResponseBuilder(data)
            builder.parse_request()

            qname = builder.qname.lower().rstrip(".")
            qtype = builder.qtype
            zone = self.zone_database.extract_zone(qname)

            # Check if we are authoritative for this zone
            if zone not in self.zone_database.zones:
                print(f"[DNS] Refusing query for unknown zone: {zone}")
                return builder.build_response(aa=0, rcode=5, zone_name="", ip=None)

            ip = self.zone_database.lookup(qname)

            # Standard A Record Query (Type 1)
            if qtype == 1:
                if ip:
                    print(f"[DNS] Found record: {qname} -> {ip}")
                    return builder.build_response(aa=1, rcode=0, zone_name=zone, ip=ip)
                else:
                    print(f"[DNS] NXDOMAIN for: {qname}")
                    return builder.build_response(aa=1, rcode=3, zone_name=zone, include_soa=True,
                                                  soa_data=self.zone_database.get_soa(qname))

            # Handle other types as No Data (RCODE 0 but no answer section)
            return builder.build_response(aa=1, rcode=0, zone_name=zone, include_soa=True,
                                          soa_data=self.zone_database.get_soa(qname))

        except Exception as e:
            print(f"ERROR: {e}")  # Debugging point for 'ZoneDatabase' object errors
            transaction_id = int.from_bytes(data[0:2], byteorder='big')
            # Return SERVFAIL (RCODE 2) on internal error
            return struct.pack("!HHHHHH", transaction_id, (1 << 15) | 2, 1, 0, 0, 0)


if __name__ == "__main__":
    # Standard DNS is port 53; using 8053 for your lab environment
    transport = UdpTransport("127.0.0.1", 8053)
    transport.initialize()

    # Load the zone data from your dns.json file
    database = ZoneDatabase("dns.json")
    server = DNSServer(database)

    print("[DNS] Server is ready to handle requests.")
    try:
        while True:
            data, addr = transport.receive()
            if data:
                response = server.handle_request(data)
                transport.send(response, addr)
    except KeyboardInterrupt:
        print("\n[DNS] Shutting down...")
        transport.close()