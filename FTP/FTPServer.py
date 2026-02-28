import base64
import socket
import json
import threading
import time


class FTPServer:
    def __init__(self, host='0.0.0.0'):
        self.host = host
        self.control_port = 2121

        # הגדרות RUDP (מבוסס על ערכי ברירת מחדל)
        self.max_msg_size = 60000  # גודל צ'אנק (קרוב ל-64KB)
        self.sliding_window = 5  # גודל חלון
        self.timeout = 2.0  # זמן המתנה ל-ACK בשניות

    def start_server(self):
        # 1. יצירת Listening Socket ב-TCP (ערוץ הבקרה)
        welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        welcome_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # מאפשר הרצה חוזרת מהירה
        welcome_sock.bind((self.host, self.control_port))
        welcome_sock.listen(5)
        print(f"Control Channel listening on TCP port {self.control_port}...")

        while True:
            try:
                # המתנה לחיבור קליינט
                control_conn, addr = welcome_sock.accept()
                print(f"New connection from {addr}")

                # קבלת פקודת JSON בערוץ הבקרה
                data = control_conn.recv(1024).decode('utf-8')
                if not data:
                    continue

                request = json.loads(data)
                mode = request.get("mode")  # "TCP" או "RUDP"
                filename = request.get("filename")

                if mode == "RUDP":
                    # שליחת הטיפול ב-RUDP ל-Thread נפרד כדי לא לחסום את השרת
                    threading.Thread(target=self.handle_rudp_transfer, args=(control_conn, filename, addr)).start()
                else:
                    self.handle_tcp_transfer(control_conn, filename)

            except Exception as e:
                print(f"Main Loop Error: {e}")

    def handle_rudp_transfer(self, control_conn, filename, client_addr):
        """שליחת קובץ ב-RUDP אמין עם Sliding Window"""
        print(f"Opening RUDP Sender for {filename} to {client_addr}")

        # 1. יצירת סוקט UDP להעברת הנתונים
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data_sock.bind((self.host, 0))
        data_port = data_sock.getsockname()[1]

        try:
            # 2. הודעה ללקוח דרך ה-TCP באיזה פורט UDP להאזין
            response = json.dumps({"status": "ready", "mode": "RUDP", "data_port": data_port})
            control_conn.send(response.encode('utf-8'))
            control_conn.close()  # סיימנו עם ערוץ הבקרה עבור בקשה זו

            # 3. קריאת הקובץ ופירוק לפאקטים
            with open(filename, "rb") as f:
                file_bytes = f.read()

            packets = []
            packet_counter = 0
            temp_bytes = file_bytes
            while temp_bytes:
                chunk = temp_bytes[:self.max_msg_size]
                temp_bytes = temp_bytes[self.max_msg_size:]
                packet = {
                    "type": "DATA",
                    "num": packet_counter,
                    "payload": base64.b64encode(chunk).decode("ascii")
                }
                packets.append(packet)
                packet_counter += 1

            total_packets = len(packets)
            print(f"File split into {total_packets} packets.")

            # 4. ניהול משתני חלון
            last_ack = -1
            next_to_send = 0
            timer = None
            lock = threading.Lock()  # להגנה על משתנה ה-last_ack

            def ack_receiver():
                nonlocal last_ack
                data_sock.settimeout(self.timeout)
                while last_ack < total_packets - 1:
                    try:
                        raw_ack, _ = data_sock.recvfrom(1024)
                        ans = json.loads(raw_ack.decode('utf-8'))
                        if ans.get("type") == "ACK":
                            received_num = ans.get("num")
                            with lock:
                                if received_num > last_ack:
                                    last_ack = received_num
                                    print(f"ACK received for packet {last_ack}")
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"ACK Receiver error: {e}")
                        break

            # הפעלת Thread להאזנה ל-ACKs
            threading.Thread(target=ack_receiver, daemon=True).start()

            # 5. לולאת השליחה (Sliding Window)
            client_udp_endpoint = (client_addr[0], 5556)  # הלקוח מאזין בפורט הקבוע שלו

            while last_ack < total_packets - 1:
                with lock:
                    start_of_window = last_ack + 1
                    end_of_window = min(start_of_window + self.sliding_window - 1, total_packets - 1)

                # שליחת פאקטים בחלון
                if next_to_send <= end_of_window:
                    msg = (json.dumps(packets[next_to_send]) + "\n").encode("utf-8")
                    data_sock.sendto(msg, client_udp_endpoint)

                    if next_to_send == start_of_window:
                        timer = time.perf_counter()
                    next_to_send += 1

                # בדיקת Timeout
                if timer and (time.perf_counter() - timer > self.timeout):
                    print(f"Timeout! Resending from packet {start_of_window}")
                    next_to_send = start_of_window
                    timer = time.perf_counter()

                time.sleep(0.001)  # מניעת עומס על ה-CPU

            # 6. סיום
            data_sock.sendto(json.dumps({"type": "END"}).encode("utf-8"), client_udp_endpoint)
            print(f"Transfer of {filename} via RUDP complete.")

        except FileNotFoundError:
            print(f"File {filename} not found.")
        except Exception as e:
            print(f"RUDP Transfer Error: {e}")
        finally:
            data_sock.close()

    def handle_tcp_transfer(self, control_conn, filename):
        """העברה ב-TCP רגיל"""
        print(f"Transferring {filename} via standard TCP...")
        try:
            data_welcome_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_welcome_sock.bind((self.host, 0))
            data_port = data_welcome_sock.getsockname()[1]
            data_welcome_sock.listen(1)

            response = json.dumps({"status": "ready", "mode": "TCP", "data_port": data_port})
            control_conn.send(response.encode('utf-8'))

            data_conn, addr = data_welcome_sock.accept()
            with open(filename, "rb") as f:
                while chunk := f.read(4096):
                    data_conn.sendall(chunk)

            print(f"Finished sending {filename}")
            data_conn.close()
            data_welcome_sock.close()
            control_conn.close()

        except FileNotFoundError:
            control_conn.send(json.dumps({"status": "error", "message": "File not found"}).encode('utf-8'))
        except Exception as e:
            print(f"TCP Transfer Error: {e}")


if __name__ == "__main__":
    server = FTPServer()
    server.start_server()