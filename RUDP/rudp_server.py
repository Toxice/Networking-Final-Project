import socket
import threading
import time
import json
from .rudp_protocol import RUDPProtocol


class RUDPServer:
    def __init__(self, host, port, window_size=5, timeout=1.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.window_size = window_size
        self.timeout = timeout
        self.last_ack = -1
        self.lock = threading.Lock()

    def send_file(self, file_bytes, client_addr):
        """Sends file bytes using a sliding window after receiving a client trigger."""
        # 1. WAIT FOR CLIENT TRIGGER (Handshake)
        print(f"[RUDP] Server listening on {self.sock.getsockname()}, waiting for client trigger...")
        try:
            # We wait for any packet from the client to 'lock in' the destination
            _, actual_client_addr = self.sock.recvfrom(1024)
            print(f"[RUDP] Trigger received from {actual_client_addr}. Starting transfer.")
        except Exception as e:
            print(f"[RUDP] Failed to receive trigger: {e}")
            return

        # 2. PREPARE PACKETS
        packets = [file_bytes[i:i + RUDPProtocol.MAX_PACKET_SIZE]
                   for i in range(0, len(file_bytes), RUDPProtocol.MAX_PACKET_SIZE)]
        total_packets = len(packets)
        next_to_send = 0
        self.last_ack = -1

        # 3. ACK LISTENER THREAD
        def listen_for_acks():
            self.sock.settimeout(self.timeout)
            while self.last_ack < total_packets - 1:
                try:
                    data, _ = self.sock.recvfrom(1024)
                    msg = json.loads(data.decode())
                    if msg.get("type") == "ACK":
                        with self.lock:
                            # Cumulative ACK logic
                            self.last_ack = max(self.last_ack, msg.get("num"))
                except (socket.timeout, json.JSONDecodeError):
                    continue

        ack_thread = threading.Thread(target=listen_for_acks, daemon=True)
        ack_thread.start()

        # 4. SLIDING WINDOW SEND LOOP
        while self.last_ack < total_packets - 1:
            with self.lock:
                upper_bound = min(self.last_ack + self.window_size, total_packets - 1)

            while next_to_send <= upper_bound:
                packet = RUDPProtocol.create_packet(next_to_send, total_packets, packets[next_to_send])
                self.sock.sendto(packet, actual_client_addr)
                next_to_send += 1

            time.sleep(0.01)  # Flow control to prevent CPU exhaustion

            # Timeout/Retransmission logic
            if self.last_ack < next_to_send - self.window_size:
                next_to_send = self.last_ack + 1

        # 5. FINALIZE
        for _ in range(5):
            self.sock.sendto(b"DONE", actual_client_addr)

        print(f"[RUDP] Transfer complete. Sent {total_packets} packets.")
        self.sock.close()