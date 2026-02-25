# ftp_server.py

import ftp_server_protocol
import socket
import threading
import argparse

"""
FTP state machine:
    1. get a request to send a file
    2. find the file
    3. send a response stating the file is found with its byte size
    4. start sending the file
    5. once all bytes were sent - send another response stating that
    6. client asks to quit
    7. server sends a teardown response and closing the data socket, until the next time
"""

def serve(host, port):
    """
    this function is meant to start the server, will be executed by main
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    print(f"[FTP] Listening on {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def handle_client(conn:socket.socket, addr):
    pass
    """
    this function handles the FTP state machine
    """

def main():
    ap = argparse.ArgumentParser(description="JSON FTP Server")
    ap.add_argument("--host", default="127.0.0.0", help="IP address for the server")
    ap.add_argument("--port", default=2121, help="port for the server, avoid using known ports like 80,8080,21 etc")