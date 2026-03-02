#header
class DNSHeader:

    def __init__(self,raw_data):
        self.raw_data = raw_data
        #parsing fixed 12-byte header
        self.transaction_id = int.from_bytes(self.raw_data[0:2], "big")
        self.flags = int.from_bytes(self.raw_data[2:4],byteorder='big')
        self.qdcount = int.from_bytes(self.raw_data[4:6], byteorder='big')
        self.ancount = int.from_bytes(self.raw_data[6:8], byteorder='big')
        self.nscount = int.from_bytes(self.raw_data[8:10], byteorder='big')
        self.arcount = int.from_bytes(self.raw_data[10:12], byteorder='big')

        #extracting flag bits
        self.qr = (self.flags >> 15) & 1
        self.opcode = (self.flags >> 11) & 0b1111
        self.aa = (self.flags >> 10) & 1
        self.tc = (self.flags >> 9) & 1
        self.rd = (self.flags >> 8) & 1
        self.ra = (self.flags >> 7) & 1
        self.z = (self.flags >> 4) & 0b111
        self.rcode = self.flags & 0b1111

