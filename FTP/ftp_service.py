import socket
import json
import struct
import sys


class FTPService:
    CONTROL_PORT = 2121
    BUFFER_SIZE = 65535

    def __init__(self, server_ip, client_ip):
        self.server_ip = server_ip
        self.client_ip = client_ip

    def run_file_transfer(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as control_sock:
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
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as ds:
            ds.bind((self.client_ip, 0))
            ds.sendto(json.dumps({"type": "ACK", "num": -1}).encode(), (self.server_ip, port))

            received = {}
            total = 0
            ds.settimeout(5)
            try:
                while True:
                    data, addr = ds.recvfrom(self.BUFFER_SIZE)
                    if data == b"DONE": break
                    p_num, total = struct.unpack("!II", data[:8])
                    if p_num not in received:
                        received[p_num] = data[8:]
                        sys.stdout.write(f"\rProgress: {len(received)}/{total}")
                    ds.sendto(json.dumps({"type": "ACK", "num": p_num}).encode(), addr)
            except socket.timeout:
                pass

            with open(path, 'wb') as f:
                for i in sorted(received.keys()): f.write(received[i])
        print(f"\nSaved: {path}")