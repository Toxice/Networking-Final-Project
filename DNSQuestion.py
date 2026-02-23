class DNSQuestion:

    def __init__(self,raw_data):
        self.raw_data = raw_data

    def parse_question(self,start_index):
        #qname
        labels  = []
        found_terminator = False
        total_length = 0
        i = start_index
            #checking bounds
        if i >= len(self.raw_data):
            raise ValueError("QNAME out of bounds. malformed data")
            #maximum length of dns label
        while i < len(self.raw_data):
            length = self.raw_data[i]
            if length == 0:
                found_terminator = True
                i = i + 1
                break
            if length > 63:
                raise ValueError("label is too long. trying hack me?")
            if i + 1 + length > len(self.raw_data):
                raise ValueError("buffer overrun. malformed data")
            total_length += length + 1
            if total_length > 255:
                raise ValueError("maximum length is 255. malformed data")
            labels.append(self.raw_data[i + 1 : i + 1 + length].decode())
            i = i + 1 + length
        if not found_terminator:
            raise ValueError("missing zero terminator in QNAME malformed data")
            #checking whether we have at least 4 bytes left
        next_offset = i
        if next_offset + 4 > len(self.raw_data):
            raise ValueError("no bytes for qtype and qclass. malformed data")
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