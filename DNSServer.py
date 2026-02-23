from xml.etree.ElementInclude import include

from DNSResponseBuilder import DNSResponseBuilder

class DNSServer:
    def __init__(self, zone_database):
        self.zone_database = zone_database
    def handle_request(self, data):
        builder = DNSResponseBuilder(data)
        builder.parse_request()

        qname = builder.qname
        qtype = builder.qtype

        # 1. Authority check
        #REFUSED -- not in out database
        # we dont work with google.com
        if not self.zone_database.is_in_zone(qname):
            include_soa=False
            rcode = 5
            aa = 0 #authoritive answer
            ip = None
        #in the database
        else:
            #for any name inside our zone
            # 2. Type check (only support A) ipv4
            #we dont support AAAA ipv6
            if qtype != 1:
                include_soa = True
                rcode = 0
                aa = 1
                ip = None

            else:
                # we got example.com
                ip = self.zone_database.lookup(qname)

                #in our zone. NOERROR
                if ip is not None:
                    include_soa = False
                    rcode = 0
                    aa = 1
                #NXDOMAIN
                else:
                    include_soa = True
                    rcode = 3
                    aa = 1

        if include_soa:
            soa_data = self.zone_database.get_soa()
        else:
            soa_data = None

        return builder.build_response(aa, rcode, self.zone_database.get_name(),include_soa, ip, soa_data)
