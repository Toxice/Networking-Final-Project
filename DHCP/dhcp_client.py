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

def serve():
    """
    sets up the socket for sending
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # broadcast
    print(f"[Client] Sending Data Across Port {OUT_PORT}...")
    sock.sendto()

def main():
    serve()

if __name__ == "__main__":
    main()
