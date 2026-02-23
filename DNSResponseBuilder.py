import socket

from DNSQuestion import DNSQuestion
from UdpTransport import UdpTransport
from ZoneDatabase import ZoneDatabase
import struct


class DNSResponseBuilder:
    def __init__(self,request_data):
        self.request_data = request_data

        #parsed data
        self.transaction_id = None
        self.flags = None
        self.qname = None
        self.qtype = None
        self.qclass = None

    #same parsing as in question
    def parse_request(self):
        self.transaction_id = int.from_bytes(self.request_data[0:2],byteorder='big')
        self.flags = int.from_bytes(self.request_data[2:4],byteorder='big')
        question = DNSQuestion(self.request_data)
        self.qname, self.qtype, self.qclass, self.offset = question.parse_question(12)

    #building dns header for response
    def build_header(self, ancount, rcode, aa, nscount):
        # Extract RD from request (bit 8)
        rd = (self.flags >> 8) & 1
        # Build flags from scratch
        response_flags = 0
        # QR = 1 (response)
        response_flags |= (1 << 15)
        # OPCODE = 0 (standard query) → leave 0
        # AA (authoritative answer)
        if aa:
            response_flags |= (1 << 10)
        # TC = 0 (no truncation)
        # RD → copy from request
        if rd:
            response_flags |= (1 << 8)
        # RA = 0 (no recursion available)
        # Z = 0 (must be zero)
        # RCODE (lower 4 bits)
        response_flags |= rcode


        header = struct.pack(
            "!HHHHHH", #! for big endian, H = unsigned short, L - unsigned long
            self.transaction_id,
            response_flags,
            1,  # QDCOUNT
            ancount,  # ANCOUNT - answer count. how many answer records are in the Answer section
            nscount,  # NSCOUNT
            0  # ARCOUNT
        )
        return header #pack returns bytes!

     #copying question section. this section must match the request exactly
     #if client asked example.com TYPE A CLASS IN we are to copy this!
    def build_question_section(self):
        return self.request_data[12:self.offset]

    #building full structure for answer
    def build_answer_section(self, ip):

        if ip is None:
            return b''

        if self.qtype ==1 and self.qclass ==1:
            #TYPE A, CLASS IN
            #building answer: NAME|TYPE|CLASS|TTL|RDLENGTH|RDATA
            aname = 0xC00C #pointer to self.qname
            atype = 1
            aclass = 1
            attl = 300
            ardlength = 4
            ardata = socket.inet_aton(ip)

            answer = struct.pack(
                "!HHHLH4s",
                aname,
                atype,
                aclass,
                attl,
                ardlength,
                ardata
            )
            return answer  #pack returns bytes!
        #not answer
        else:
            return b'' #empty bytes object

    #function to encode dns name to format b'\x03ns1\x07example\x03com\x00
    def encode_dns_name(self, dns_name):
        dns_name = dns_name.lower().rstrip(".")
        labels = dns_name.split('.')

        encoded = b''
        for label in labels:
            length = len(label)   #taking length of label "ns1" = 3
            encoded +=bytes([length]) #converting to 1 byte
            encoded += label.encode() #add and encode
        encoded += b'\x00'
        return encoded

    #building soa itself. we have 5 fixed size integers + dynamic mname and rname
    def build_soa_record(self, soa_dict, zone_name):
        soa_ints = struct.pack("!IIIII", soa_dict.get("serial"),
                               soa_dict.get("refresh"),
                               soa_dict.get("retry"),
                               soa_dict.get("expire"),
                               soa_dict.get("minimum"))
        encoded_mname = self.encode_dns_name(soa_dict.get("mname"))
        encoded_rname = self.encode_dns_name(soa_dict.get("rname"))

        rdata = encoded_mname + encoded_rname + soa_ints
        rdlength = len(rdata)

        # NAME|TYPE|CLASS|TTL|RDLENGTH|RDATA
        #encoded zone name for authority section
        encoded_name = self.encode_dns_name(zone_name)
        #type = 6, class = 1, ttl = 300
        return (
            encoded_name + struct.pack("!HHIH",6,1,300,rdlength) + rdata
        )

        #packing up everything 2gether
        # HEADER|QUESTION|ANSWER|AUTHORITY|ADDITIONAL(dont have)
    def build_response(self, aa, rcode, zone_name, include_soa=False, ip = None, soa_data = None):
        self.parse_request()


        #working with soa for NXDOMAIN AND NODATA
        """FINISH SOA"""
        if include_soa:
            nscount = 1
            authority = self.build_soa_record(soa_data, zone_name )
        else:
            nscount = 0
            authority = b''

        if ip is not None:
            ancount = 1
        else:
            ancount = 0


        question = self.build_question_section()
        answer = self.build_answer_section(ip)

        header = self.build_header(ancount, rcode, aa, nscount)

        return header + question + answer + authority











        
