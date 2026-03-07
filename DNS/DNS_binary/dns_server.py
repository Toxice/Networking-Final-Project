import socket
import random
import time
import struct
from dns_protocol import *

# a class for working with raw socket
class UdpTransport:
    #constructor
    def __init__(self, host, port, timeout = 2, buffer_size = 1024, receive_loss_rate=0.0,
                 send_loss_rate = 0.0, artificial_delay_ms = 0):
        self.host = host #ip
        self.port = port
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.receive_loss_rate = receive_loss_rate
        self.send_loss_rate = send_loss_rate
        self.artificial_delay_ms = artificial_delay_ms

        self.sock = None
        self.running = False

        #opening socket itself
    def initialize(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #udp ipv4
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(self.timeout)
        self.running = True
        print(f"UDP server running on {self.host}:{self.port}")

    def receive(self):
        try:
            data, addr = self.sock.recvfrom(self.buffer_size) #raw bytes of data + addr of sender in a tuple
            #simulation incoming packet loss
            if random.random() < self.receive_loss_rate:
                print("Dropped incoming packet")
                return None, None
            if self.artificial_delay_ms > 0:
                time.sleep(self.artificial_delay_ms/1000)
            return data, addr
        except socket.timeout:
            return None, None
        except Exception as e:
            print(f"Receive error: {e}")
            return None, None

    def send(self, data, addr):
        if random.random() < self.send_loss_rate:
            print("Dropped outgoing packet")
            return
        if self.artificial_delay_ms > 0:
            time.sleep(self.artificial_delay_ms/1000)
        try:
            self.sock.sendto(data, addr)
        except Exception as e:
            print(f"Send error: {e}")

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()


#main logic
import struct

class DNSServer:
    def __init__(self, zone_database):
        self.zone_database = zone_database

    def handle_request(self, data):

        if data is None:
            return b''

            # Reject oversized UDP packets (standard DNS limit = 512 bytes)
        if len(data) > 512:
            transaction_id = int.from_bytes(data[0:2], byteorder='big') if len(data) >= 2 else 0
            flags = (1 << 15) | 1  # QR=1, RCODE=1 (FORMERR)
            return struct.pack("!HHHHHH", transaction_id, flags, 0, 0, 0, 0)

        if len(data) < 12:
            transaction_id = int.from_bytes(data[0:2], byteorder='big') if len(data) >= 2 else 0
            flags = (1 << 15) | 1  # FORMERR
            return struct.pack("!HHHHHH", transaction_id, flags, 0, 0, 0, 0)

        try:
            builder = DNSResponseBuilder(data)
            builder.parse_request()

            qname = builder.qname.lower().rstrip(".")
            qtype = builder.qtype

            ip = self.zone_database.lookup(qname)

            # NOT authoritative → REFUSED
            zone = self.zone_database.extract_zone(qname)

            if zone not in self.zone_database.database:
                # not authoritative
                return builder.build_response(
                    aa=0,
                    rcode=5,  # REFUSED
                    zone_name="",
                    include_soa=False,
                    ip=None,
                    soa_data=None
                )

            # Only support A
            if qtype != 1:
                return builder.build_response(
                    aa=1,
                    rcode=0,
                    zone_name=self.zone_database.extract_zone(qname),
                    include_soa=True,
                    ip=None,
                    soa_data=self.zone_database.get_soa(qname)
                )

            # Record exists
            if ip:
                return builder.build_response(
                    aa=1,
                    rcode=0,
                    zone_name=self.zone_database.extract_zone(qname),
                    include_soa=False,
                    ip=ip,
                    soa_data=None
                )

            # Inside zone but missing → NXDOMAIN
            return builder.build_response(
                aa=1,
                rcode=3,
                zone_name=self.zone_database.extract_zone(qname),
                include_soa=True,
                ip=None,
                soa_data=self.zone_database.get_soa(qname)
            )

        except Exception as e:
            print("ERROR:", e)  # <-- important for debugging
            transaction_id = int.from_bytes(data[0:2], byteorder='big')
            flags = (1 << 15) | 2  # SERVFAIL
            return struct.pack("!HHHHHH", transaction_id, flags, 0, 0, 0, 0)



if __name__ == "__main__":
    transport = UdpTransport("127.0.0.1", 8053)
    transport.initialize()

    database = ZoneDatabase()
    server = DNSServer(database)

    while True:
        data, addr = transport.receive()
        if data is None:
            continue

        response = server.handle_request(data)
        transport.send(response, addr)


