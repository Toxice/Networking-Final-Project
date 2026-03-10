import socket
import json
import threading
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RUDP.rudp_server import RUDPServer  # Import the extracted protocol


class FTPServer:
    def __init__(self, host='0.0.0.0'):
        self.host = host
        self.control_port = 2121
        self.music_dir = "server_music"

        # Note: sliding_window and timeout are now handled inside RUDPServer

        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)
            print(f"Created directory: {self.music_dir}")

    def get_music_list(self):
        """Scans the directory for supported file types."""
        valid_extensions = ('.mp3', '.jpg', '.JPG', '.jpeg', '.gif', '.mp4')
        files = [f for f in os.listdir(self.music_dir) if f.endswith(valid_extensions)]
        return files[:10]

    def start_server(self):
        welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        welcome_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        welcome_sock.bind((self.host, self.control_port))
        welcome_sock.listen(5)
        print(f"FTP Server is up! Control Channel on port {self.control_port}")

        while True:
            try:
                control_conn, addr = welcome_sock.accept()
                print(f"\n[Control] Connected to {addr}")

                # 1. Send Menu
                music_list = self.get_music_list()
                menu_data = json.dumps({"type": "MENU", "files": music_list})
                control_conn.send((menu_data + "\n").encode('utf-8'))

                # 2. Receive Request
                raw_request = control_conn.recv(1024).decode('utf-8')
                if not raw_request:
                    continue

                request = json.loads(raw_request)
                filename = request.get("filename")
                mode = request.get("mode")

                file_path = os.path.join(self.music_dir, filename)

                if not os.path.exists(file_path):
                    error_msg = json.dumps({"status": "error", "message": "File not found"})
                    control_conn.send(error_msg.encode('utf-8'))
                    control_conn.close()
                    continue

                # 3. Route to Transfer Mode
                if mode == "RUDP":
                    # RUDP transfer runs in its own thread to not block the control channel
                    threading.Thread(target=self.handle_rudp_transfer, args=(control_conn, file_path, addr)).start()
                else:
                    self.handle_tcp_transfer(control_conn, file_path)

            except Exception as e:
                print(f"Server Error: {e}")

    def handle_tcp_transfer(self, control_conn, file_path):
        """Standard TCP file transfer."""
        print(f"[TCP] Starting transfer for: {file_path}")
        try:
            data_welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_welcome_sock.bind((self.host, 0))
            data_port = data_welcome_sock.getsockname()[1]
            data_welcome_sock.listen(1)

            response = json.dumps({"status": "ready", "mode": "TCP", "data_port": data_port})
            control_conn.send(response.encode('utf-8'))

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
        """Reliable UDP transfer using the encapsulated RUDPServer protocol."""
        print(f"[RUDP] Initializing protocol for: {file_path}")

        # We need a temporary port to tell the client where to connect
        # We'll let RUDPServer handle the actual binding
        try:
            # 1. Create the RUDP Server instance (it binds to a port automatically)
            # You can pass window_size or timeout here if your RUDPServer __init__ supports it
            rudp_handler = RUDPServer(self.host, 0)
            data_port = rudp_handler.sock.getsockname()[1]

            # 2. Inform client of the UDP port
            response = json.dumps({"status": "ready", "mode": "RUDP", "data_port": data_port})
            control_conn.send(response.encode('utf-8'))
            control_conn.close()

            # 3. Read file into memory (common for lab-scale RUDP)
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # 4. Delegate the heavy lifting to the protocol layer
            # Note: We pass the client_addr to the send_file method
            # In your RUDP implementation, ensure it waits for a 'handshake' or 'trigger'
            # from the client to confirm the client's dynamic UDP port.
            rudp_handler.send_file(file_bytes, client_addr)

            print(f"[RUDP] Protocol finished sending {file_path}")

        except Exception as e:
            print(f"[RUDP] Error: {e}")


if __name__ == "__main__":
    server = FTPServer()
    server.start_server()