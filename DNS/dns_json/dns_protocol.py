from dns_server import *
import json


#databasex
class ZoneDatabase:
    #new def init:
    def __init__(self, file_path="dns.json"):
        self.file_path = file_path
        self._load()

        # self.name = None
        # self.soa = None

        # opeling a file with our database

    def _load(self):
        try:
            with open(self.file_path, "r") as f:
                self.database = json.load(f)
        except FileNotFoundError:
            self.database = {}

    # writing python dict into the database.json
    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.database, f, indent=4)

    # adding new data into database
    def add_record(self, url: str, ip: str):
        normalized = url.lower().rstrip(".")
        # ipv4
        try:
            socket.inet_aton(ip)  # converting string into bytes
        except OSError:  # catching errors
            raise ValueError("invalid ipv4 address")

        self.database[normalized] = ip
        self._save()

    #checking whether name is in records:
    def is_in_zone(self, name):
        normalized_name = name.lower().rstrip(".")
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

