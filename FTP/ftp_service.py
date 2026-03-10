import socket
import json
import os
from RUDP.rudp_service import RUDPService


class FTPService:
    CONTROL_PORT = 2121
    BUFFER_SIZE = 65535

    def __init__(self, server_ip, client_ip):
        self.server_ip = server_ip
        self.client_ip = client_ip

    def _receive_tcp(self, port, path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ds:
            ds.connect((self.server_ip, port))
            with open(path, "wb") as f:
                while chunk := ds.recv(8192):
                    f.write(chunk)
        print(f"TCP Download Complete: {path}")

    def _receive_rudp(self, port, path):
        server_data_addr = (self.server_ip, port)
        client = RUDPService(self.client_ip, server_data_addr)
        file_data = client.receive_file()
        with open(path, 'wb') as f:
            f.write(file_data)
        print(f"\nRUDP Download Complete: {path}")

    def run_file_transfer(self):
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            control_sock.connect((self.server_ip, self.CONTROL_PORT))
            while True:
                choice = input("\nWelcome, for quitting - press QUIT else press FTP: ").lower().strip()
                control_sock.send(choice.encode('utf-8'))

                if choice == "quit":
                    break

                if choice == "ftp":
                    # Receive Menu
                    raw_menu = control_sock.recv(self.BUFFER_SIZE).decode('utf-8')
                    menu = json.loads(raw_menu)
                    files = menu.get("files", [])

                    for i, f in enumerate(files):
                        print(f"{i + 1}. {f}")

                    idx = int(input("\nSelect file number: ")) - 1
                    mode = input("Select mode (TCP/RUDP): ").upper().strip()
                    selected_file = files[idx]

                    # Send Request
                    control_sock.send(json.dumps({"filename": selected_file, "mode": mode}).encode('utf-8'))

                    # Receive Port Info
                    resp_raw = control_sock.recv(self.BUFFER_SIZE).decode('utf-8')
                    resp = json.loads(resp_raw)

                    if resp.get("status") == "ready":
                        out_path = f"downloaded_{selected_file}"
                        port = resp.get("data_port")

                        if mode == "TCP":
                            self._receive_tcp(port, out_path)
                        else:
                            self._receive_rudp(port, out_path)
                    else:
                        print(f"Server Error: {resp.get('message')}")

        except Exception as e:
            print(f"FTP Client Error: {e}")
        finally:
            control_sock.close()