import socket
import json
import random
import uuid
import struct
import sys

# Magic Numbers
DHCP_SERVER_PORT = 6767
DHCP_CLIENT_PORT = 6868
DNS_SERVER_PORT = 8053
CONTROL_PORT = 2121
BROADCAST_IP = '255.255.255.255'
BUFFER_SIZE = 65535  # גודל מקסימלי למניעת WinError 10040
TIMEOUT_SECONDS = 5
MAX_RETRIES = 5
HOSTNAME = "ftp.example.com"


class FTPClient:
    def __init__(self):
        self.assigned_ip = None
        self.dns_server_ip = None
        self.app_server_ip = None
        self.transaction_id = random.randint(1000, 9999)
        self.mac_address = self._get_mac()

    def _get_mac(self):
        """משיכת כתובת ה-MAC של המחשב"""
        mac_int = uuid.getnode()
        mac_hex = iter(hex(mac_int)[2:].zfill(12))
        return ":".join(a + b for a, b in zip(mac_hex, mac_hex)).upper()

    # --- שלב 1: DHCP ---
    def run_dhcp_process(self):
        print("--- Starting DHCP Process ---")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            sock.bind(('', DHCP_CLIENT_PORT))
        except Exception as e:
            print(f"Warning: Port {DHCP_CLIENT_PORT} bind failed: {e}")

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"DHCP Attempt {attempt}...")
            self._send_dhcp_discover(sock)

            temp_ip = self._receive_offer(sock)
            if temp_ip:
                self._send_dhcp_request(sock, temp_ip)
                if self._receive_dhcp_ack(sock):
                    print(f"Successfully bound to IP: {self.assigned_ip}")
                    sock.close()
                    return True

        print("Failed to acquire IP from DHCP.")
        sock.close()
        return False

    def _send_dhcp_discover(self, sock):
        payload = {"message_type": "DISCOVER",
                   "transaction_id": self.transaction_id,
                   "client_mac": self.mac_address}
        sock.sendto(json.dumps(payload).encode('utf-8'), (BROADCAST_IP, DHCP_SERVER_PORT))

    def _receive_offer(self, sock):
        sock.settimeout(TIMEOUT_SECONDS)
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            offer = json.loads(data.decode('utf-8'))
            if offer.get("transaction_id") == self.transaction_id and offer.get("message_type") == "OFFER":
                return offer.get("ip_address")
        except:
            return None

    def _send_dhcp_request(self, sock, offered_ip):
        payload = {"message_type": "REQUEST",
                   "transaction_id": self.transaction_id,
                   "requested_ip": offered_ip}
        sock.sendto(json.dumps(payload).encode('utf-8'), (BROADCAST_IP, DHCP_SERVER_PORT))

    def _receive_dhcp_ack(self, sock):
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            ack = json.loads(data.decode('utf-8'))
            if ack.get("transaction_id") == self.transaction_id and ack.get("message_type") == "ACK":
                self.assigned_ip = ack.get("ip_address")
                self.dns_server_ip = ack.get("dns_server")
                return True
        except:
            return False

    # --- שלב 2: DNS (Binary) ---
    def get_server_address(self, hostname):
        if not self.dns_server_ip:
            print("No DNS server IP available.")
            return None

        print(f"--- Resolving {hostname} via Standard DNS ---")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT_SECONDS)

        query = self.build_dns_query(hostname)

        for attempt in range(MAX_RETRIES):
            try:
                sock.sendto(query, (self.dns_server_ip, DNS_SERVER_PORT))
                data, _ = sock.recvfrom(BUFFER_SIZE)

                if len(data) >= 16:
                    self.app_server_ip = socket.inet_ntoa(data[-4:])
                    print(f"DNS Resolved: {hostname} -> {self.app_server_ip}")
                    sock.close()
                    return self.app_server_ip
            except Exception as e:
                print(f"DNS attempt {attempt + 1} failed: {e}")
                continue

        sock.close()
        return None

    def build_dns_query(self, hostname):
        header = struct.pack("!HHHHHH", self.transaction_id, 0x0100, 1, 0, 0, 0)
        question = b''
        for part in hostname.split('.'):
            question += struct.pack("!B", len(part)) + part.encode()
        question += b'\x00'
        question += struct.pack("!HH", 1, 1)
        return header + question

    # --- שלב 3: FTP Control & Data ---
    def request_file(self):
        if not self.app_server_ip:
            return

        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            control_sock.connect((self.app_server_ip, CONTROL_PORT))

            # קבלת תפריט
            raw_menu = control_sock.recv(BUFFER_SIZE).decode('utf-8').strip()
            menu = json.loads(raw_menu)

            if menu.get("type") == "MENU":
                files = menu.get("files", [])
                print("\n--- Available Files ---")
                for i, f in enumerate(files):
                    print(f"{i + 1}. {f}")

                choice = int(input("\nSelect file number: ")) - 1
                selected_file = files[choice]
                mode = input("Select transfer mode (TCP/RUDP): ").upper()

                control_sock.send(json.dumps({"filename": selected_file, "mode": mode}).encode('utf-8'))
                response = json.loads(control_sock.recv(BUFFER_SIZE).decode('utf-8'))

                if response.get("status") == "ready":
                    data_port = response.get("data_port")
                    output_name = f"downloaded_{selected_file}"

                    if mode == "TCP":
                        self.receive_file_tcp(data_port, output_name)
                    elif mode == "RUDP":
                        self.receive_file_rudp(data_port, output_name)

        except Exception as e:
            print(f"Request error: {e}")
        finally:
            control_sock.close()

    def receive_file_tcp(self, data_port, save_path):
        print(f"Receiving via TCP on port {data_port}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_sock:
                data_sock.connect((self.app_server_ip, data_port))
                with open(save_path, "wb") as f:
                    while True:
                        chunk = data_sock.recv(8192)
                        if not chunk: break
                        f.write(chunk)
            print(f"File saved to {save_path}")
        except Exception as e:
            print(f"TCP error: {e}")

    def receive_file_rudp(self, data_port, save_path):
        """קבלת קובץ ב-RUDP עם מד התקדמות (Progress Bar)"""
        print(f"Receiving via RUDP on port {data_port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
            client_sock.bind((self.assigned_ip, 0))
            client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)

            # שליחת ACK ראשוני
            init_ack = json.dumps({"type": "ACK", "num": -1})
            client_sock.sendto(init_ack.encode('utf-8'), (self.app_server_ip, data_port))

            client_sock.settimeout(5)
            received_packets = {}
            total_expected = 0

            try:
                while True:
                    data, addr = client_sock.recvfrom(BUFFER_SIZE)
                    if data == b"DONE": break

                    if len(data) >= 8:
                        p_num, total_expected = struct.unpack("!II", data[:8])

                        if p_num not in received_packets:
                            received_packets[p_num] = data[8:]

                            # הדפסת אחוזי הורדה בשורה אחת שמתעדכנת
                            if total_expected > 0:
                                percent = (len(received_packets) / total_expected) * 100
                                sys.stdout.write(
                                    f"\rDownloading: [{len(received_packets)}/{total_expected}] {percent:.1f}%")
                                sys.stdout.flush()

                        # שליחת ACK
                        ack = json.dumps({"type": "ACK", "num": p_num})
                        client_sock.sendto(ack.encode('utf-8'), addr)

                        if len(received_packets) == total_expected:
                            client_sock.settimeout(1)
            except socket.timeout:
                print("\nRUDP collection finished.")

            if received_packets:
                print("\nSorting and saving file...")
                with open(save_path, 'wb') as f:
                    for i in sorted(received_packets.keys()):
                        f.write(received_packets[i])
                print(f"File saved to {save_path}")



if __name__ == "__main__":
    client = FTPClient()
    if client.run_dhcp_process():
        if client.get_server_address(HOSTNAME):
            client.request_file()