import json
import socket


# Database class to handle the dns.json file
class ZoneDatabase:
    def __init__(self, file_path="dns.json"):
        self.file_path = file_path
        self.database = {}
        self._load()

    def _load(self):
        try:
            with open(self.file_path, "r") as f:
                self.database = json.load(f)
        except FileNotFoundError:
            print(f"[DNS System] Warning: {self.file_path} not found. Starting with empty database.")
            self.database = {}

    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.database, f, indent=4)

    def add_record(self, url: str, ip: str):
        normalized = url.lower().rstrip(".").strip()
        try:
            socket.inet_aton(ip)
        except OSError:
            raise ValueError("invalid ipv4 address")

        self.database[normalized] = ip
        self._save()

    def is_in_zone(self, name):
        normalized = name.lower().rstrip(".").strip()
        return normalized in self.database

    def lookup(self, domain_name):
        return self.database.get(domain_name.lower().rstrip(".").strip())


def resolve_request(database: ZoneDatabase, request_dict):
    """
    Core logic for processing the JSONClient dictionary.
    """
    # Case 1: Update/Add Record (contains both url and ip)
    if "url" in request_dict and "ip" in request_dict:
        query_url = request_dict.get("url")
        query_ip = request_dict.get("ip")

        if not isinstance(query_url, str) or not isinstance(query_ip, str):
            return {"error": "Invalid field types"}
        if not query_ip or not query_url:
            return {"error": "Invalid request format"}

        database.add_record(query_url, query_ip)
        return {"ip": database.lookup(query_url)}

    # Case 2: Standard Lookup (contains only url)
    elif "url" in request_dict:
        query_url = request_dict.get("url")
        if not isinstance(query_url, str):
            return {"error": "Invalid url type"}
        if not query_url:
            return {"ip": None}

        normalized_url = query_url.lower().rstrip(".").strip()
        ip = database.lookup(normalized_url)
        return {"ip": ip}

    else:
        return {"error": "Invalid request format"}


class json_dns_server:
    """
    The Server Wrapper handles the 'On the Wire' actions and provides 
    the commenting mechanism for visibility.
    """

    def __init__(self, zone_database):
        self.zone_database = zone_database

    def handle(self, raw_data):
        # 1. THE GATEKEEPER: Don't process empty packets or giant "bomb" packets.
        if not raw_data:
            return b''

        if len(raw_data) > 1024:
            print("[DNS] ERROR: Packet too large! Dropping it.")
            return json.dumps({"error": "Payload too large"}).encode("utf8")

        try:
            # 2. THE DECODER: Convert the "alien" bytes from the wire into a Python string.
            # Example: b'{"url": "google.com"}' -> '{"url": "google.com"}'
            decoded_string = raw_data.decode("utf8")

            # 3. THE PARSER: Turn the string into a Python Dictionary so we can read it.
            # Example: '{"url": "google.com"}' -> {"url": "google.com"}
            data = json.loads(decoded_string)

            # This is your 'commenting mechanism'—visibility into what just arrived.
            print(f"\n[DNS RECEIVE] We got a request for: {decoded_string}")

            # 4. THE BRAIN: Pass the dictionary to your 'resolve_request' function.
            # This is where the actual lookup in dns.json happens.
            resolved_dict = resolve_request(self.zone_database, data)

            # 5. THE PACKAGER: Turn our answer back into a JSONClient string.
            # Example: {"ip": "142.250.75.110"} -> '{"ip": "142.250.75.110"}'
            final_json = json.dumps(resolved_dict)

            # Visibility into what we are sending back.
            print(f"[DNS SEND] We are replying with: {final_json}")

            # 6. THE EXPORTER: Convert the string back into bytes to send over the network.
            return final_json.encode("utf8")

        except json.JSONDecodeError:
            # If someone sends us gibberish that isn't JSONClient.
            print("[DNS] ERROR: Someone sent us something that isn't valid JSONClient!")
            return json.dumps({"error": "Invalid JSONClient"}).encode("utf8")

        except Exception as e:
            # The "Catch-All" so your server doesn't crash if something else breaks.
            print(f"[DNS] CRITICAL ERROR: {e}")
            return json.dumps({"error": "Server error"}).encode("utf8")