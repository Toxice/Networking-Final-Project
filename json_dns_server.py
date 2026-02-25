from DNS.ZoneDatabase import ZoneDatabase
from dns_service import resolve_request
import json

class json_dns_server:
    def __init__(self, zone_database):
        self.zone_database = zone_database
        self.bytes = b''

    def handle(self,raw_data):
        if len(raw_data)==0:
            return b''
        try:
            decoded_data = raw_data.decode("utf8") #decoding
            data = json.loads(decoded_data) #bytes -> string
            resolved_data = resolve_request(self.zone_database, data)
            final_data = json.dumps(resolved_data).encode("utf8") #string -> bytes + encoding
            return final_data
        except Exception:
            data = {"ip": None}
            return json.dumps(data).encode("utf8")





