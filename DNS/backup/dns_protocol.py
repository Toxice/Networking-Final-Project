from dns_server import *
import json


#database
class ZoneDatabase:
    #new def init:
    def __init__(self):
        self.database = {
            "example.com": "127.0.0.1",
            "www.example.com": "127.0.0.2",
            "mail.example.com": "127.0.0.3",
            "ftp.example.com": "127.0.0.4",
            "ns1.example.com": "127.0.0.5",
            "ariel.example.com": "127.0.0.6",
            "pornhub.com": "66.254.114.41",
            "www.pornhub.com": "66.254.114.42",
            "google.com": "142.250.75.110",
            "www.google.com": "142.250.75.111",
            "ftp.google.com": "142.250.75.112"
        }

    #adding new data into database
    def add_record(self, url:str, ip:str):
        self.database[url] = ip

    #checking whether name is in records:
    def is_in_zone(self, name):
        normalized_name = name.lower().rstrip(".")
        #if normalized_name == self.zone_name:
        if normalized_name in self.database:
            return True
        elif normalized_name.endswith( "." + self.database.get(normalized_name)):
            return True
        else:
            return False

    def lookup(self, domain_name):
        return self.database.get(domain_name.lower().rstrip("."))


def resolve_request(database: ZoneDatabase, request_dict):
    #suka lets work on second url request blyatb
    if "url" in request_dict and "ip" in request_dict: #for treating stuff like { "url" : ""}
        query_url = request_dict.get("url")
        query_ip = request_dict.get("ip")
        if not query_ip or not query_url:
            print("Wrong request format")
            return {"error": "Invalid request format"}
        database.add_record(query_url, query_ip)
        ip = database.lookup(query_url)
        return {"ip": ip}
    elif "url" in request_dict:
        query_url = request_dict.get("url")
        if not query_url:
            return {"ip": None}
        normalized_url = query_url.lower().rstrip(".")
        if database.is_in_zone(normalized_url):
            ip = database.lookup(normalized_url)
            if ip:
                return {"ip": ip}
            else:
                return {"ip": None}
        else:
            return {"ip": None}
    else:
        print("ERROR")
        return {"error": "Invalid request format"}

class json_dns_server:
    def __init__(self, zone_database):
        self.zone_database = zone_database
        self.bytes = b''

    def handle(self, raw_data):
        if len(raw_data) == 0:
            return b''
        try:
            decoded_data = raw_data.decode("utf8")  # decoding
            data = json.loads(decoded_data)  # bytes -> string
            resolved_data = resolve_request(self.zone_database, data)
            final_data = json.dumps(resolved_data).encode("utf8")  # string -> bytes + encoding
            return final_data
        except Exception:
            data = {"ip": None}
            return json.dumps(data).encode("utf8")

