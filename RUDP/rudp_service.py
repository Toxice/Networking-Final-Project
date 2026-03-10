import socket
import sys
from .rudp_protocol import RUDPProtocol


class RUDPService:
    def __init__(self, client_ip, server_addr, timeout=5.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to 0 to let OS pick an ephemeral port
        self.sock.bind((client_ip, 0))
        self.server_addr = server_addr
        self.sock.settimeout(timeout)

    def receive_file(self):
        """Signals the server to start and collects incoming packets."""
        # 1. SEND TRIGGER TO SERVER
        # This tells the server we are 'listening' and opens the NAT/Firewall path
        trigger = RUDPProtocol.create_ack(-1)
        self.sock.sendto(trigger, self.server_addr)
        print(f"[RUDP] Sent trigger to {self.server_addr}, waiting for data...")

        received_chunks = {}
        total = 0

        # 2. RECEIVE LOOP
        try:
            while True:
                try:
                    data, addr = self.sock.recvfrom(RUDPProtocol.MAX_PACKET_SIZE + 64)
                    if data == b"DONE":
                        break

                    seq, total, chunk = RUDPProtocol.parse_packet(data)
                    if seq not in received_chunks:
                        received_chunks[seq] = chunk
                        sys.stdout.write(f"\rRUDP Progress: {len(received_chunks)}/{total}")
                        sys.stdout.flush()

                    # Send ACK for the received packet
                    self.sock.sendto(RUDPProtocol.create_ack(seq), addr)
                except socket.timeout:
                    if not received_chunks:
                        print("\n[RUDP] Initial connection timeout - Server didn't respond.")
                    else:
                        print("\n[RUDP] Transfer timed out mid-stream.")
                    break
        except Exception as e:
            print(f"\n[RUDP] Receiver Error: {e}")

        # 3. RECONSTRUCT
        full_data = b""
        if received_chunks:
            for i in range(len(received_chunks)):
                if i in received_chunks:
                    full_data += received_chunks[i]

        self.sock.close()
        return full_data