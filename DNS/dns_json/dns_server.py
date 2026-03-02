import socket
import random
import time


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


def run_dns_server(host: str, port: int, zone_name: str):
    transport = UdpTransport(host, port)
    transport.initialize()

    zone_database = ZoneDatabase(zone_name)
    json_server = json_dns_server(zone_database)

    while True:
        try:
            data, addr = transport.receive()
        except Exception:
            continue
        if not data:
            continue
        response = json_server.handle(data)
        transport.send(response, addr)

def serve():
    run_dns_server("127.0.0.1", 9000, "example.com")

if __name__ == "__main__":
    serve()
