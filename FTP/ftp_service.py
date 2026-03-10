import socket
import json
import struct
import sys
from RUDP.rudp_service import RUDPService


class FTPService:
    CONTROL_PORT = 2121
    BUFFER_SIZE = 65535

    def __init__(self, server_ip, client_ip):
        self.server_ip = server_ip
        self.client_ip = client_ip

    def run_file_transfer(self):
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as control_sock:
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            choice = str(input("Welcome, for quitting - press QUIT else press FTP:\n")).lower()
            if choice == "quit":
                control_sock.close()
                quit(0)
            else:
                try:
                    control_sock.connect((self.server_ip, self.CONTROL_PORT))

                    # Get Menu
                    menu = json.loads(control_sock.recv(self.BUFFER_SIZE).decode('utf-8'))
                    files = menu.get("files", [])
                    for i, f in enumerate(files): print(f"{i + 1}. {f}")

                    choice = int(input("\nSelect file number: ")) - 1
                    mode = input("Select mode (TCP/RUDP): ").upper()
                    selected_file = files[choice]

                    control_sock.send(json.dumps({"filename": selected_file, "mode": mode}).encode('utf-8'))
                    resp = json.loads(control_sock.recv(self.BUFFER_SIZE).decode('utf-8'))

                    if resp.get("status") == "ready":
                        out_path = f"downloaded_{selected_file}"
                        if mode == "TCP":
                            self._receive_tcp(resp.get("data_port"), out_path)
                        else:
                            self._receive_rudp(resp.get("data_port"), out_path)
                except Exception as e:
                    print(f"FTP Error: {e}")

    def _receive_tcp(self, port, path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ds:
            ds.connect((self.server_ip, port))
            with open(path, "wb") as f:
                while chunk := ds.recv(8192): f.write(chunk)
        print(f"Saved: {path}")

    def _receive_rudp(self, port, path):
        server_data_addr = (self.server_ip, port)
        # Create RUDP Client instance
        client = RUDPService(self.client_ip, server_data_addr)

        # Receive the raw bytes
        file_data = client.receive_file()

        with open(path, 'wb') as f:
            f.write(file_data)
        print(f"\nSaved via RUDP: {path}")