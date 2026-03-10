import socket
import json
import threading
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from RUDP.rudp_server import RUDPServer


class FTPServer:
    def __init__(self, host='0.0.0.0'):
        self.host = host
        self.control_port = 2121
        self.file_dir = "server_files"

        if not os.path.exists(self.file_dir):
            os.makedirs(self.file_dir)

    def get_file_list(self):
        valid_extensions = ('.mp3', '.jpg', '.JPG', '.jpeg', '.gif', '.mp4')
        return [f for f in os.listdir(self.file_dir) if f.endswith(valid_extensions)][:10]

    def start_server(self):
        welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        welcome_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        welcome_sock.bind((self.host, self.control_port))
        welcome_sock.listen(5)
        print(f"[FTP] Server listening on port {self.control_port}")

        while True:
            control_conn, addr = welcome_sock.accept()
            print(f"[Control] Connected by {addr}")
            threading.Thread(target=self.handle_client_session, args=(control_conn, addr)).start()

    def handle_client_session(self, control_conn, addr):
        with control_conn:
            while True:
                try:
                    # Wait for command: 'ftp' or 'quit'
                    data = control_conn.recv(1024).decode('utf-8').strip()
                    if not data or data.lower() == 'quit':
                        break

                    if data.lower() == 'ftp':
                        # Send Menu only when requested
                        file_list = self.get_file_list()
                        menu_data = json.dumps({"type": "MENU", "files": file_list})
                        control_conn.send((menu_data + "\n").encode("utf-8"))

                        # Receive File Request
                        raw_request = control_conn.recv(1024).decode("utf-8")
                        if not raw_request: break

                        request = json.loads(raw_request)
                        filename = request.get("filename")
                        mode = request.get("mode")
                        file_path = os.path.join(self.file_dir, filename)

                        if not os.path.exists(file_path):
                            control_conn.send(
                                json.dumps({"status": "error", "message": "File not found"}).encode("utf-8"))
                            continue

                        if mode == "RUDP":
                            self.handle_rudp_transfer(control_conn, file_path, addr)
                        else:
                            self.handle_tcp_transfer(control_conn, file_path)

                except Exception as e:
                    print(f"Session Error: {e}")
                    break

    def handle_tcp_transfer(self, control_conn, file_path):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_welcome_sock:
                data_welcome_sock.bind((self.host, 0))
                data_port = data_welcome_sock.getsockname()[1]
                data_welcome_sock.listen(1)

                response = json.dumps({"status": "ready", "mode": "TCP", "data_port": data_port})
                control_conn.send(response.encode('utf-8'))

                data_conn, _ = data_welcome_sock.accept()
                with data_conn, open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        data_conn.sendall(chunk)
            print(f"[TCP] Finished: {file_path}")
        except Exception as e:
            print(f"[TCP] Error: {e}")

    def handle_rudp_transfer(self, control_conn, file_path, client_addr):
        try:
            rudp_handler = RUDPServer(self.host, 0)
            data_port = rudp_handler.sock.getsockname()[1]

            response = json.dumps({"status": "ready", "mode": "RUDP", "data_port": data_port})
            control_conn.send(response.encode('utf-8'))

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            rudp_handler.send_file(file_bytes, client_addr)
            print(f"[RUDP] Finished: {file_path}")
        except Exception as e:
            print(f"[RUDP] Error: {e}")


if __name__ == "__main__":
    FTPServer().start_server()