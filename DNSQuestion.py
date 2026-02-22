class DNSQuestion:

    def __init__(self,raw_data):
        self.raw_data = raw_data

    def parse_question(self,start_index):
        #qname
        labels  = []
        i = start_index
        while self.raw_data[i] != 0:
            length = self.raw_data[i]
            labels.append(self.raw_data[i+1:i + 1 + length].decode())
            i = i + 1 + length
        next_offset = i + 1
        #qtype
        qtype = int.from_bytes(self.raw_data[next_offset:next_offset + 2],byteorder='big')
        qclass = int.from_bytes(self.raw_data[next_offset+2:next_offset + 4],byteorder='big')
        next_offset = next_offset + 4
        return ".".join(labels),qtype,qclass,next_offset
"""
if __name__ == "__main__":
    raw_packet = (
        b'\x00' * 12 +               # fake 12-byte header
        b'\x07example\x04comc\x00' +  # QNAME
        b'\x00\x01' +                # QTYPE (A)
        b'\x00\x01'                  # QCLASS (IN)
    )
    question = DNSQuestion(raw_packet)
    domain, offset = question.parse_qname(12)
    print("Domain:", domain)
    print("Offset:", offset)
"""