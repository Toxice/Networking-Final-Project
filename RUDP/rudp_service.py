import socket
import sys
from .rudp_protocol import RUDPProtocol


class RUDPService:
    def __init__(self, client_ip, server_addr, timeout=5.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((client_ip, 0))
        self.server_addr = server_addr
        self.sock.settimeout(timeout)

    def receive_file(self):
        # 1. SEND SYN TRIGGER
        trigger = RUDPProtocol.create_packet(0, 0, b"", flags=RUDPProtocol.SYN_FLAG)
        self.sock.sendto(trigger, self.server_addr)
        print(f"[RUDP] Sent SYN to {self.server_addr}, waiting for data...")

        received_chunks = {}
        total = 0

        # 2. RECEIVE LOOP
        try:
            while True:
                try:
                    data, addr = self.sock.recvfrom(RUDPProtocol.MAX_PAYLOAD_SIZE + 64)
                    parsed = RUDPProtocol.parse_packet(data)
                    if not parsed: continue

                    seq, total, flags, chunk = parsed

                    # Check for FIN
                    if flags & RUDPProtocol.FIN_FLAG:
                        print("\n[RUDP] FIN received. Closing.")
                        break

                    # Store Data
                    if seq not in received_chunks:
                        received_chunks[seq] = chunk
                        sys.stdout.write(f"\rRUDP Progress: {len(received_chunks)}/{total}")
                        sys.stdout.flush()

                    # Send Binary ACK
                    ack_packet = RUDPProtocol.create_ack(seq)
                    self.sock.sendto(ack_packet, addr)

                except socket.timeout:
                    if not received_chunks:
                        print("\n[RUDP] Connection timeout - No response.")
                    else:
                        print("\n[RUDP] Stream timed out.")
                    break
        except Exception as e:
            print(f"\n[RUDP] Receiver Error: {e}")

        # 3. RECONSTRUCT
        full_data = b""
        if received_chunks:
            for i in range(max(received_chunks.keys()) + 1):
                if i in received_chunks:
                    full_data += received_chunks[i]

        self.sock.close()
        return full_data