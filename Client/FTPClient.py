import socket
import json
import random
import uuid

# Magic Numbers
DHCP_SERVER_PORT = 67
DHCP_CLIENT_PORT = 68
DNS_SERVER_PORT = 53
CONTROL_PORT = 2121
BROADCAST_IP = '255.255.255.255'
BUFFER_SIZE = 1024
TIMEOUT_SECONDS = 5
MAX_RETRIES = 5
HOSTNAME = "FTP.server"


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
        payload = {"message_type": "DISCOVER", "transaction_id": self.transaction_id, "client_mac": self.mac_address}
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
        payload = {"message_type": "REQUEST", "transaction_id": self.transaction_id, "requested_ip": offered_ip}
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

    # --- שלב 2: DNS ---
    def get_server_address(self, hostname):
        if not self.dns_server_ip:
            print("No DNS server IP available.")
            return None

        print(f"--- Resolving {hostname} via DNS ---")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        for _ in range(MAX_RETRIES):
            payload = {"message_type": "REQUEST", "transaction_id": self.transaction_id, "hostname": hostname}
            sock.sendto(json.dumps(payload).encode('utf-8'), (self.dns_server_ip, DNS_SERVER_PORT))

            sock.settimeout(TIMEOUT_SECONDS)
            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                ans = json.loads(data.decode('utf-8'))
                if ans.get("transaction_id") == self.transaction_id:
                    self.app_server_ip = ans.get("ip_address")
                    print(f"DNS Resolved: {hostname} -> {self.app_server_ip}")
                    sock.close()
                    return self.app_server_ip
            except:
                continue

        sock.close()
        return None

    # --- שלב 3: FTP Control & Data ---
    def request_file(self, filename, mode="TCP"):
        if not self.app_server_ip:
            print("Error: No server IP. Did DNS fail?")
            return

        # 1. ערוץ בקרה (Control Channel) - תמיד TCP
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            control_sock.connect((self.app_server_ip, CONTROL_PORT))
            request_data = {"filename": filename, "mode": mode}
            control_sock.send(json.dumps(request_data).encode('utf-8'))

            response = json.loads(control_sock.recv(BUFFER_SIZE).decode('utf-8'))

            if response.get("status") == "ready":
                data_port = response.get("data_port")
                output_name = f"downloaded_{filename}"

                if mode == "TCP":
                    self.receive_file_tcp(data_port, output_name)
                else:
                    self.receive_file_udp(data_port, output_name)
            else:
                print(f"Server error: {response.get('message')}")

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            control_sock.close()

    def receive_file_tcp(self, data_port, save_path):
        print(f"Receiving via TCP on port {data_port}...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_sock:
                data_sock.connect((self.app_server_ip, data_port))
                with open(save_path, "wb") as f:
                    while True:
                        chunk = data_sock.recv(4096)
                        if not chunk: break
                        f.write(chunk)
            print(f"File saved to {save_path}")
        except Exception as e:
            print(f"TCP Transfer error: {e}")

    def receive_file_udp(self, data_port, save_path):
        print(f"Receiving via UDP on port {data_port}...")
        # שים לב: ב-UDP הקליינט מאזין בדרך כלל או שולח חבילה ראשונה לשרת כדי "לפתוח" את הדרך
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
            client_sock.bind(("", data_port))
            client_sock.settimeout(10)  # טיימאאוט אם השרת לא שולח כלום

            with open(save_path, 'wb') as f:
                while True:
                    try:
                        data, addr = client_sock.recvfrom(4096)
                        if not data or data == b"DONE":
                            break
                        f.write(data)
                    except socket.timeout:
                        print("UDP Transfer timed out.")
                        break
        print(f"File saved to {save_path}")


if __name__ == "__main__":
    client = FTPClient()
    if client.run_dhcp_process():
        if client.get_server_address(HOSTNAME):
            file_to_get = input("File name (e.g. song.mp3): ")
            mode = input("Mode (TCP/RUDP): ").upper()
            client.request_file(file_to_get, mode)