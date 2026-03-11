import socket
import threading
import time
from .rudp_protocol import RUDPProtocol


class RUDPServer:
    def __init__(self, host, port, window_size=10, timeout=1.0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.window_size = window_size
        self.timeout = timeout
        self.last_ack = -1
        self.lock = threading.Lock()
        self.total_packets = 0

    def send_file(self, file_bytes, client_addr=None):
        print(f"[RUDP] Server listening on {self.sock.getsockname()}...")

        # 1. WAIT FOR SYN TRIGGER
        try:
            data, actual_client_addr = self.sock.recvfrom(1024)
            _, _, flags, _ = RUDPProtocol.parse_packet(data)
            if not (flags & RUDPProtocol.SYN_FLAG):
                print("[RUDP] Invalid trigger received. Expected SYN.")
                return
            print(f"[RUDP] SYN received from {actual_client_addr}. Starting transfer.")
        except Exception as e:
            print(f"[RUDP] Trigger error: {e}")
            return

        # 2. PREPARE DATA
        packets = [file_bytes[i:i + RUDPProtocol.MAX_PAYLOAD_SIZE]
                   for i in range(0, len(file_bytes), RUDPProtocol.MAX_PAYLOAD_SIZE)]
        self.total_packets = len(packets)
        next_to_send = 0
        self.last_ack = -1

        # 3. BINARY ACK LISTENER
        def listen_for_acks():
            self.sock.settimeout(self.timeout)
            while True:
                with self.lock:
                    if self.last_ack >= self.total_packets - 1:
                        break
                try:
                    data, _ = self.sock.recvfrom(1024)
                    res = RUDPProtocol.parse_packet(data)
                    if res:
                        seq, _, flags, _ = res
                        if flags & RUDPProtocol.ACK_FLAG:
                            with self.lock:
                                self.last_ack = max(self.last_ack, seq)
                except socket.timeout:
                    continue
                except Exception:
                    break

        ack_thread = threading.Thread(target=listen_for_acks, daemon=True)
        ack_thread.start()

        # 4. SLIDING WINDOW LOOP
        while True:
            with self.lock:
                if self.last_ack >= self.total_packets - 1:
                    break
                upper_bound = min(self.last_ack + self.window_size, self.total_packets - 1)

            while next_to_send <= upper_bound:
                packet = RUDPProtocol.create_packet(next_to_send, self.total_packets, packets[next_to_send])
                self.sock.sendto(packet, actual_client_addr)
                next_to_send += 1

            time.sleep(0.005)

            # Retransmission logic
            with self.lock:
                if self.last_ack < next_to_send - self.window_size:
                    next_to_send = self.last_ack + 1

        # 5. FINALIZE WITH BINARY FIN
        fin_packet = RUDPProtocol.create_packet(self.total_packets, self.total_packets, b"",
                                                flags=RUDPProtocol.FIN_FLAG)
        for _ in range(5):
            self.sock.sendto(fin_packet, actual_client_addr)
            time.sleep(0.01)

        print(f"[RUDP] Transfer complete. Sent {self.total_packets} packets.")
        self.sock.close()