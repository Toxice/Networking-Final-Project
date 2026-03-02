from DNS.DNS_binary.delete_this_shit.UdpTransport import UdpTransport
from DNS.DNS_binary.delete_this_shit.ZoneDatabase import (ZoneDatabase)
from DNS.DNS_json.delete_this_shitr.json_dns_server import json_dns_server


def run_dns_server(host:str, port:int, zone_name:str):
    transport = UdpTransport(host, port)
    transport.initialize()

    zone_database = ZoneDatabase(zone_name)
    json_server = json_dns_server(zone_database)

    while True:
        try:
            data,addr = transport.receive()
        except Exception:
           continue
        if not data:
            continue
        response = json_server.handle(data)
        transport.send(response, addr)