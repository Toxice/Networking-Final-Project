import socket
import json
import threading
import time
import os
import struct


class FTPServer:
    def __init__(self, host='127.0.0.1'):
        self.host = host
        self.control_port = 2121
        self.music_dir = "server_music"  # התיקייה עם השירים
        self.max_msg_size = 30000  # גודל חבילה ל-RUDP
        self.sliding_window = 5  # גודל חלון
        self.timeout = 2.0  # זמן המתנה ל-ACK

        # יצירת התיקייה אם היא לא קיימת
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)
            print(f"Created directory: {self.music_dir}. Please put your MP3 files there.")

    def get_music_list(self):
        """סורק את התיקייה ומחזיר רשימה של עד 3 שירים"""
        files = [f for f in os.listdir(self.music_dir) if f.endswith('.mp3')]
        return files[:3]

    def start_server(self):
        # יצירת Socket לערוץ הבקרה (TCP)
        welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        welcome_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        welcome_sock.bind((self.host, self.control_port))
        welcome_sock.listen(5)
        print(f"FTP Server is up! Control Channel on port {self.control_port}")

        while True:
            try:
                control_conn, addr = welcome_sock.accept()
                print(f"\n[Control] Connected to {addr}")

                # 1. שליחת תפריט השירים לקליינט מיד עם החיבור
                music_list = self.get_music_list()
                menu_data = json.dumps({"type": "MENU", "files": music_list})
                control_conn.send((menu_data + "\n").encode('utf-8'))

                # 2. קבלת הבקשה מהקליינט (איזה קובץ ובאיזה מצב)
                raw_request = control_conn.recv(1024).decode('utf-8')
                if not raw_request:
                    continue

                request = json.loads(raw_request)
                filename = request.get("filename")
                mode = request.get("mode")  # "TCP" או "RUDP"

                file_path = os.path.join(self.music_dir, filename)

                if not os.path.exists(file_path):
                    error_msg = json.dumps({"status": "error", "message": "File not found on server"})
                    control_conn.send(error_msg.encode('utf-8'))
                    control_conn.close()
                    continue

                # 3. ניתוב להעברה המתאימה
                if mode == "RUDP":
                    threading.Thread(target=self.handle_rudp_transfer, args=(control_conn, file_path, addr)).start()
                elif mode == "TCP":
                    self.handle_tcp_transfer(control_conn, file_path)

            except Exception as e:
                print(f"Server Error: {e}")

    def handle_tcp_transfer(self, control_conn, file_path):
        """העברת קובץ ב-TCP סטנדרטי"""
        print(f"[TCP] Starting transfer for: {file_path}")
        try:
            # פתיחת פורט נתונים דינמי
            data_welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_welcome_sock.bind((self.host, 0))
            data_port = data_welcome_sock.getsockname()[1]
            data_welcome_sock.listen(1)

            # שליחת הפורט לקליינט
            response = json.dumps({"status": "ready", "mode": "TCP", "data_port": data_port})
            control_conn.send(response.encode('utf-8'))

            # קבלת חיבור בפורט הנתונים
            data_conn, addr = data_welcome_sock.accept()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    data_conn.sendall(chunk)

            print(f"[TCP] Finished sending {file_path}")
            data_conn.close()
            data_welcome_sock.close()
            control_conn.close()
        except Exception as e:
            print(f"[TCP] Error: {e}")

    def handle_rudp_transfer(self, control_conn, file_path, client_addr):
        """Fixed RUDP Transfer with Handshake and Address Binding"""
        print(f"[RUDP] Starting transfer for: {file_path}")
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to 0.0.0.0 to ensure we receive the client's UDP packets
        data_sock.bind(('0.0.0.0', 0))
        data_port = data_sock.getsockname()[1]

        try:
            # Send port to client and close control connection
            response = json.dumps({"status": "ready", "mode": "RUDP", "data_port": data_port})
            control_conn.send((response + "\n").encode('utf-8'))
            control_conn.close()

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            packets = [file_bytes[i:i + self.max_msg_size] for i in range(0, len(file_bytes), self.max_msg_size)]
            total_packets = len(packets)

            last_ack = -1
            next_to_send = 0
            client_data_endpoint = None
            lock = threading.Lock()

            def ack_receiver():
                nonlocal last_ack, client_data_endpoint
                data_sock.settimeout(self.timeout)
                while last_ack < total_packets - 1:
                    try:
                        raw_ack, addr = data_sock.recvfrom(65535)
                        if client_data_endpoint is None:
                            client_data_endpoint = addr  # Identify client's UDP port

                        ans = json.loads(raw_ack.decode('utf-8'))
                        if ans.get("type") == "ACK":
                            with lock:
                                last_ack = max(last_ack, ans.get("num"))
                    except:
                        continue

            threading.Thread(target=ack_receiver, daemon=True).start()

            # HANDSHAKE WAIT: Don't start sending until client contacts the UDP port
            print("[RUDP] Waiting for client UDP handshake...")
            while client_data_endpoint is None:
                time.sleep(0.1)

            while last_ack < total_packets - 1:
                with lock:
                    end_of_window = min(last_ack + self.sliding_window, total_packets - 1)

                while next_to_send <= end_of_window:
                    header = struct.pack("!II", next_to_send, total_packets)
                    data_sock.sendto(header + packets[next_to_send], client_data_endpoint)
                    next_to_send += 1

                time.sleep(0.01)

                # Timeout Retransmission
                with lock:
                    if last_ack < next_to_send - self.sliding_window:
                        next_to_send = last_ack + 1

            for _ in range(5):
                data_sock.sendto(b"DONE", client_data_endpoint)
            print(f"[RUDP] Finished sending {file_path}")

        except Exception as e:
            print(f"[RUDP] Error: {e}")
        finally:
            data_sock.close()


if __name__ == "__main__":
    # Change '127.0.0.1' to '0.0.0.0' to accept connections from any interface
    server = FTPServer(host='0.0.0.0')
    server.start_server()