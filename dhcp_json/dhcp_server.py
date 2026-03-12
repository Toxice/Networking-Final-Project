"""
dhcp_server.py - CLI entrypoint for DHCPServer

Usage:
    python dhcp_server.py --ip-mask <mask> --allocation <count> --dns <dns_ip>

Example:
    python dhcp_server.py --ip-mask 192.168.1 --allocation 50 --dns 10.100.102.5
"""

import argparse
from dhcp_protocol import DHCPServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start a DHCP server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ip-mask",
        type=str,
        default="10.100.102",
        help="24-bit IP prefix for the address pool (e.g. '192.168.1').",
    )
    parser.add_argument(
        "--allocation",
        type=int,
        default=10,
        help="Number of IPs to allocate (2–256).",
    )
    # Added the --dns argument to support your static DNS requirement
    parser.add_argument(
        "--dns",
        type=str,
        default=None,
        help="Static DNS IP to provide to clients (overrides dhcp.json if provided).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # The server initialization now passes all three parameters to the DHCPServer class
    server = DHCPServer(
        ip_mask=args.ip_mask,
        allocation=args.allocation,
        dns=args.dns
    )

    print(
        f"[DHCP] Starting server | "
        f"mask={args.ip_mask}.0/24 | "
        f"pool={args.allocation} IPs | "
        f"DNS={server.dns_server}"
    )

    # Start the infinite network loop
    try:
        server.serve()
    except KeyboardInterrupt:
        print("\n[DHCP] Server shutting down manually.")


if __name__ == "__main__":
    main()