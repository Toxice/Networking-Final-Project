import json
from DNS.ZoneDatabase import ZoneDatabase

def resolve_request(database:ZoneDatabase, request_dict):
    url = request_dict.get("url")
    if not url:
        return {"ip": None}
    normalized_url = url.lower().rstrip(".")
    if database.is_in_zone(normalized_url):
        ip = database.lookup(normalized_url)
        if ip:
            return { "ip": ip }
        else:
            return { "ip": None }
    else:
        return { "ip": None }
