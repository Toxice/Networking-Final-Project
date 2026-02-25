import socket
import json


class FTPServer:
    def __init__(self, host='0.0.0.0'):
        self.control_port = 2121
        self.host = host

    def start_server(self):
        # 1. יצירת Listening Socket ב-TCP (ערוץ הבקרה)
        welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        welcome_sock.bind((self.host, self.control_port))
        welcome_sock.listen(5)
        print(f"Control Channel listening on TCP port {self.control_port}...")

        while True:
            # המתנה לחיבור קליינט
            control_conn, addr = welcome_sock.accept()
            print(f"New connection from {addr}")

            try:
                # קבלת פקודת JSON בערוץ הבקרה
                data = control_conn.recv(1024).decode('utf-8')
                request = json.loads(data)

                # החלטה על סוג ערוץ הנתונים
                mode = request.get("mode")  # "TCP" או "RUDP"
                filename = request.get("filename")

                if mode == "RUDP":
                    self.handle_rudp_transfer(filename, addr)
                else:
                    self.handle_tcp_transfer(control_conn, filename)

                control_conn.close()  # סגירת ערוץ הבקרה בסיום
            except Exception as e:
                print(f"Error: {e}")

    def handle_rudp_transfer(self, filename, client_addr):
        """פתיחת סוקט UDP חדש לגמרי עבור העברת ה-MP3"""
        print(f"Opening RUDP Data Channel for {filename}...")
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # כאן תבוא לוגיקת ה-reliable_send שבנינו קודם
        # שימי לב: client_addr[0] הוא ה-IP של הלקוח
        pass

    def handle_tcp_transfer(self, control_conn, filename):
        """העברה ב-TCP רגיל (יכול להיות על אותו סוקט או חדש)"""
        print(f"Transferring {filename} via standard TCP...")
        pass