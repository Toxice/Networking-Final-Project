"""
we need:
    1. UDP socket listening on port 67
    2. UDP socket as client on port 68
    3. we need a hold a set of IP addresses, of like 100 addresses
    4. each time we allocate an address we need to mark it as in use, and count for the amount of time it's in use
    5. we only need to implement the DHCP server, the DHCP client will be embedded into the general client
"""

import argparse
import socket

IN_ADDRESS = "0.0.0.0"
OUT_ADDRESS = "255.255.255.255"
IN_PORT = 67
OUT_PORT = 68

def serve(host:str):
    """
    sets up the socket for listening
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # broadcast
    sock.bind((IN_ADDRESS, IN_PORT))
    print(f"[DHCP] Listening on {IN_ADDRESS} on Port {IN_PORT}...")
    while True:
        data, address = sock.recvfrom(1024)
        print("[DHCP] received a request for IP allocation")

        response = build_dhcp_data()

        dest = ("255.255.255.255", OUT_PORT)
        sock.sendto(response, dest)

def main():
    ap = argparse.ArgumentParser(description="DHCP Server")
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    serve(args.host)

def build_dhcp_data():
    return b""

if __name__ == "__main__":
    main()
