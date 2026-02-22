from UdpTransport import UdpTransport
from ZoneDatabase import ZoneDatabase
from DNSServer import DNSServer

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
