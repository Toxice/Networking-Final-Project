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
        print(f"DNS server running on {self.host}:{self.port}")

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
        #working with bad input
        if data is None:
            return b''
        if len(data) < 12:
            if len(data) < 2:
                return b''
            else:
                transaction_id = int.from_bytes(data[0:2],byteorder='big')
                flags = (1 << 15) | 1  # QR=1, RCODE=1
                return struct.pack("!HHHHHH", transaction_id, flags, 0, 0, 0, 0)


        try:
            builder = DNSResponseBuilder(data)
            builder.parse_request()

            qname = builder.qname
            qtype = builder.qtype

            # 1. Authority check
            #REFUSED -- not in out database
            # we dont work with google.com
            if not self.zone_database.is_in_zone(qname):
                include_soa=False
                rcode = 5
                aa = 0 #authoritive answer
                ip = None
            #in the database
            else:
                #for any name inside our zone
                # 2. Type check (only support A) ipv4
                #we dont support AAAA ipv6
                if qtype != 1:
                    include_soa = True
                    rcode = 0
                    aa = 1
                    ip = None

                else:
                    # we got example.com
                    ip = self.zone_database.lookup(qname)

                    #in our zone. NOERROR
                    if ip is not None:
                        include_soa = False
                        rcode = 0
                        aa = 1
                    #NXDOMAIN
                    else:
                        include_soa = True
                        rcode = 3
                        aa = 1

            if include_soa:
                soa_data = self.zone_database.get_soa()
            else:
                soa_data = None

            return builder.build_response(aa, rcode, self.zone_database.get_name(),include_soa, ip, soa_data)
        except ValueError:
            transaction_id = int.from_bytes(data[0:2], byteorder='big')
            flags = (1 << 15) | 1  # QR=1, RCODE=1
            return struct.pack("!HHHHHH", transaction_id, flags, 0, 0, 0, 0)



if __name__ == "__main__":
    transport = UdpTransport("127.0.0.1", 8053)
    transport.initialize()

    database = ZoneDatabase("example.com")
    server = DNSServer(database)

    while True:
        data, addr = transport.receive()
        if data is None:
            continue

        response = server.handle_request(data)
        transport.send(response, addr)


