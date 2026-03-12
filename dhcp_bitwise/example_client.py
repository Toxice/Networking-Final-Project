import socket
import random
import dhcp_protocol
import sys

def get_mac_address():
    # Generates a random 6-byte MAC address for testing
    return bytes([0x00, 0x16, 0x3e, random.randint(0, 255),
                  random.randint(0, 255), random.randint(0, 255)])


def run_client(interface="eth0"):
    # 1. Setup Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Linux-specific interface binding
    if sys.platform.startswith('linux'):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode())
        except PermissionError:
            print("Error: DHCP Client requires sudo on Linux.")
            return

    sock.bind(('', 6868))  # DHCP Clients listen on port 68
    sock.settimeout(5)

    xid = random.randint(1, 0xFFFFFFFF)
    mac = get_mac_address()
    print(f"Client MAC: {mac.hex(':')} | XID: {hex(xid)}")

    try:
        # --- PHASE 1: DISCOVER ---
        print("Sending DISCOVER...")
        discover_pkt = dhcp_protocol.create_discover(xid, mac)
        # sock.sendto(discover_pkt, ('<broadcast>', 6767))
        sock.sendto(discover_pkt, ('127.0.0.1', 6767))

        # --- PHASE 2: OFFER ---
        data, addr = sock.recvfrom(1024)
        offer_pkt = dhcp_protocol.unpack_dhcp_packet(data)
        if offer_pkt.xid == xid:
            print(f"Received OFFER: {offer_pkt.yiaddr} from {offer_pkt.siaddr}")
        else:
            print("Received OFFER with wrong XID.")
            return

        # --- PHASE 3: REQUEST ---
        print(f"Sending REQUEST for {offer_pkt.yiaddr}...")
        request_pkt = dhcp_protocol.create_request(xid, mac, offer_pkt.yiaddr, offer_pkt.siaddr)
        # sock.sendto(request_pkt, ('<broadcast>', 6767))
        sock.sendto(request_pkt, ('127.0.0.1', 6767))

        # --- PHASE 4: ACK ---
        data, addr = sock.recvfrom(1024)
        ack_pkt = dhcp_protocol.unpack_dhcp_packet(data)
        if ack_pkt.options.get(53) == b'\x05':  # DHCP ACK
            print(f"SUCCESS! IP {ack_pkt.yiaddr} leased from {ack_pkt.siaddr}")

    except socket.timeout:
        print("Error: No response from DHCP server (Timeout).")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_client(sys.argv[1])
    else:
        run_client()