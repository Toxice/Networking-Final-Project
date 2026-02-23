from pkgutil import resolve_name


class ZoneDatabase:
    def __init__(self, name:str):
        self.zone_name = name.lower().rstrip(".")
        self.records = {
            self.zone_name : "127.0.0.1",
            "www." + self.zone_name : "127.0.0.2",
            "mail." +  self.zone_name  : "127.0.0.3",
            "ftp." +  self.zone_name  : "127.0.0.4",
            "ns1." +  self.zone_name  : "127.0.0.5",
            "pornhub." + self.zone_name : "66.254.114.41"
        }
        #SOA - start of authority
        self.soa = {
            "mname": "ns1." + self.zone_name, #primary nameserver
            "rname": "hostmaster." + self.zone_name, #responsible email
            "serial": 13121312,
            "refresh": 3600,
            "retry": 600,
            "expire": 86400,
            "minimum": 300
        }

    def get_soa(self):
        return self.soa

    #checking whether name is in records:
    def is_in_zone(self, name):
        normalized_name = name.lower().rstrip(".")
        if normalized_name == self.zone_name:
            return True
        elif normalized_name.endswith( "." + self.zone_name):
            return True
        else:
            return False
    def get_name(self):
        return self.zone_name

    def lookup(self, domain_name):
        return self.records.get(domain_name.lower().rstrip("."))