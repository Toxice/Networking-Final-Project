import socket
import json
import random
import uuid
from ftp_client_protocol import retrieve
from ftp_client_protocol import quit
import argparse

# Magic Numbers
DHCP_SERVER_PORT = 67
DHCP_CLIENT_PORT = 68
DNS_SERVER_PORT = 53
BROADCAST_IP = '255.255.255.255'
BUFFER_SIZE = 1024
TIMEOUT_SECONDS = 5
MAX_RETRIES = 5


class FTPClient:
    def __init__(self):
        self.assigned_ip = None
        self.dns_server_ip = None
        self.app_server_ip = None
        self.transaction_id = random.randint(1000, 9999) # a random session ID generator
        self.mac_address = self._get_real_mac()

    # this function is redundant, please remove it
    def _get_real_mac(self):
        """משיכת כתובת ה-MAC האמיתית של המחשב לטובת קוד כללי [cite: 4]"""
        mac_int = uuid.getnode()
        mac_hex = iter(hex(mac_int)[2:].zfill(12))
        return ":".join(a + b for a, b in zip(mac_hex, mac_hex)).upper()

    # --- שלב 1: DHCP (תהליך DORA) ---
    def run_dhcp_process(self):
        """ניהול תהליך ה-DHCP המלא כולל ניסיונות חוזרים [cite: 13, 81]"""
        print("Starting DHCP Process...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            # קישור לפורט 68 כמתחייב מהפרוטוקול
            sock.bind(('', DHCP_CLIENT_PORT))
        except Exception as e:
            print(f"Warning: Could not bind to port {DHCP_CLIENT_PORT}: {e}")

        attempt = 0
        while attempt < MAX_RETRIES:
            attempt += 1
            print(f"DHCP Attempt {attempt}...")

            # 1. Discover
            self._send_dhcp_discover(sock)

            # 2. Offer
            temp_offered_ip = self._receive_offer(sock)
            if not temp_offered_ip:
                continue

            # 3. Request
            self._send_dhcp_request(sock, temp_offered_ip)

            # 4. ACK
            if self._receive_dhcp_ack(sock):
                print(f"Successfully bound to IP: {self.assigned_ip}")
                break
        else:
            print("Failed to acquire IP from DHCP server.")

        sock.close()

    def _send_dhcp_discover(self, sock):
        """יצירה ושליחה של הודעת DISCOVER בפורמט JSON"""
        payload = {
            "message_type": "DISCOVER",
            "transaction_id": self.transaction_id,
            "client_mac": self.mac_address
        }
        sock.sendto(json.dumps(payload).encode('utf-8'), (BROADCAST_IP, DHCP_SERVER_PORT))
        print("Sent DISCOVER")

    def _receive_offer(self, sock):
        """האזנה להצעת IP מהשרת עם טיפול ב-Timeout [cite: 14]"""
        sock.settimeout(TIMEOUT_SECONDS)
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            offer = json.loads(data.decode('utf-8'))
            if offer.get("transaction_id") == self.transaction_id and offer.get("message_type") == "OFFER":
                ip = offer.get("ip_address")
                print(f"Received OFFER: {ip}")
                return ip
        except (socket.timeout, json.JSONDecodeError):
            print("Offer timeout or invalid JSON.")
        return None

    def _send_dhcp_request(self, sock, offered_ip):
        """שליחת בקשת אישור (REQUEST) עבור ה-IP שהוצע"""
        payload = {
            "message_type": "REQUEST",
            "transaction_id": self.transaction_id,
            "client_mac": self.mac_address,
            "requested_ip": offered_ip
        }
        sock.sendto(json.dumps(payload).encode('utf-8'), (BROADCAST_IP, DHCP_SERVER_PORT))
        print(f"Sent REQUEST for {offered_ip}")

    def _receive_dhcp_ack(self, sock):
        """קבלת אישור סופי (ACK) ועדכון הגדרות הרשת של הקליינט"""
        sock.settimeout(TIMEOUT_SECONDS)
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            ack = json.loads(data.decode('utf-8'))
            if ack.get("transaction_id") == self.transaction_id and ack.get("message_type") == "ACK":
                self.assigned_ip = ack.get("ip_address")
                self.dns_server_ip = ack.get("dns_server")
                return True
        except Exception:
            return False
        return False

    # --- שלב 2: DNS --- [cite: 37]
    def get_server_address(self, hostname):
        """שאילתת DNS לשרת המקומי """
        print(f"Resolving {hostname} via DNS...")
        sock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        attempt= 0

        while attempt < MAX_RETRIES:
            attempt += 1
            self.send_dns_request(hostname, sock)
            if self.receive_dns_answer(sock):
                break

        sock.close()
        return self.app_server_ip




    def send_dns_request(self, hostname, sock):
        payload = {
            "message_type": "REQUEST",
            "transaction_id": self.transaction_id,
            "hostname": hostname
        }

        sock.sendto(json.dumps(payload).encode('utf-8'), (self.dns_server_ip, DNS_SERVER_PORT))
        print("sent DNS request")

    def receive_dns_answer(self, sock):
        sock.settimeout(TIMEOUT_SECONDS)
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            ans = json.loads(data.decode('utf-8'))
            if ans.get("transaction_id") == self.transaction_id and ans.get("message_type") == "ACK":
                self.app_server_ip = ans.get("ip_address")
                return True
        except Exception:
            return False
        return False


    # --- שלב 3: Application Server (FTP) --- [cite: 37, 60]
    def connect_to_ftp_tcp(self):
        """חיבור FTP סטנדרטי מעל TCP [cite: 47]"""
        pass

    def connect_to_ftp_rudp(self):
        """מימוש FTP מעל Reliable UDP הכולל חלון דינמי ו-ACKs [cite: 48, 50]"""
        pass

    #n1k0 coding...
    def serve(self, host="127.0.0.1", port=2121):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def send_retr(self,filename, host = "127.0.0.0", port = 2121):
        retr = retrieve(filename)
        encoded_retr = json.dumps(retr).encode('utf-8')
        self.client_socket.sendto(encoded_retr,(host, port))

    def send_quit(self,filename,host = "127.0.0.0", port = 2121):
        create_quit = quit()
        encoded_quit = json.dumps(create_quit).encode('utf-8')
        self.client_socket.sendto(encoded_quit,(host, port))
    #n1k0 is done

if __name__ == "__main__":

    client = FTPClient()
    client.run_dhcp_process()