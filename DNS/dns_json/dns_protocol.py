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
        normalized = url.lower().rstrip(".").strip()
        # ipv4
        try:
            socket.inet_aton(ip)  # converting string into bytes
        except OSError:  # catching errors
            print("[DNS]")
            raise ValueError("invalid ipv4 address")

        self.database[normalized] = ip
        self._save()

    #checking whether name is in records:
    def is_in_zone(self, name):
        normalized = name.lower().rstrip(".")
        return normalized in self.database

    def lookup(self, domain_name):
        return self.database.get(domain_name.lower().rstrip("."))


def resolve_request(database: ZoneDatabase, request_dict):
    #suka lets work on second url request blyatb
    if "url" in request_dict and "ip" in request_dict: #for treating stuff like { "url" : ""}
        query_url = request_dict.get("url")
        query_ip = request_dict.get("ip")
        if not isinstance(query_url, str) or not isinstance(query_ip, str): #checking whether query_url is str
            print("[DNS]")
            return {"error": "Invalid field types"}
        if not query_ip or not query_url:
            print("[DNS]")
            print("Wrong request format")
            return {"error": "Invalid request format"}
        database.add_record(query_url, query_ip)
        ip = database.lookup(query_url)
        return {"ip": ip}
    elif "url" in request_dict:
        query_url = request_dict.get("url")
        if not isinstance(query_url, str):
            print("[DNS]")
            return {"error": "Invalid url type"}
        if not query_url:
            return {"ip": None}
        normalized_url = query_url.lower().rstrip(".").strip()
        if database.is_in_zone(normalized_url):
            ip = database.lookup(normalized_url)
            if ip:
                return {"ip": ip}
            else:
                return {"ip": None}
        else:
            return {"ip": None}
    else:
        print("[DNS]")
        print("ERROR")
        return {"error": "Invalid request format"}

class json_dns_server:
    def __init__(self, zone_database):
        self.zone_database = zone_database
        self.bytes = b''

    def handle(self, raw_data):
        #checking correct size of data
        if len(raw_data) == 1024:
            print("[DNS]")
            return json.dumps({"error": "Payload too large"}).encode("utf8")
        if len(raw_data) == 0:
            return b''
        try:
            decoded_data = raw_data.decode("utf8")  # decoding
            data = json.loads(decoded_data)  # bytes -> string
            resolved_data = resolve_request(self.zone_database, data)
            final_data = json.dumps(resolved_data).encode("utf8")  # string -> bytes + encoding
            return final_data
        except Exception as e:
            print("[DNS]")
            print("ERROR:", e)
            return json.dumps({"error": "Server error"}).encode("utf8")

