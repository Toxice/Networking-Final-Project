import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# This calculates the path to the 'Networking-Project' directory
# by going up two levels from where client.py is located.
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if root_path not in sys.path:
    sys.path.insert(0, root_path)

# ALSO add the specific folder where the DHCP logic lives
sys.path.insert(0, os.path.join(root_path, 'DHCP', 'bitwise_dhcp'))
sys.path.insert(0, os.path.join(root_path, 'DNS', 'dns_binary'))
sys.path.insert(0, os.path.join(root_path, 'FTP'))

from DHCP.bitwise_dhcp.dhcp_service import DHCPService
from DNS.DNS_binary.dns_service import DNSService
from FTP.ftp_service import FTPService

HOSTNAME = "ftp.project_gay.com"

LOCAL_IP = "127.0.0.1"


def main():
    # Phase 1: DHCP
    dhcp = DHCPService()
    assigned_ip, dns_ip = dhcp.get_ip_and_dns()

    if not assigned_ip:
        print("Failed to get IP via DHCP.")
        return

    print(f"Bound to: {assigned_ip} | DNS: {dns_ip}")

    # Phase 2: DNS
    dns = DNSService(dns_ip)
    server_ip = dns.resolve(HOSTNAME)

    if not server_ip:
        print("Could not resolve FTP server.")
        return

    # Phase 3: FTP
    # ftp = FTPService(server_ip, assigned_ip)
    ftp = FTPService(server_ip, LOCAL_IP)
    print(f"binding to {server_ip}")
    ftp.run_file_transfer()


if __name__ == "__main__":
    main()