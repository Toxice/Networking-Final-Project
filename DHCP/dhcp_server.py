"""
dhcp_server.py - CLI entrypoint for DHCPServer

Usage:
    python dhcp_server.py --ip-mask <mask> --allocation <count>

Example:
    python dhcp_server.py --ip-mask 192.168.1 --allocation 50
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
        default="127.0.0",
        help="24-bit IP prefix for the address pool (e.g. '192.168.1').",
    )
    parser.add_argument(
        "--allocation",
        type=int,
        default=10,
        help="Number of IPs to allocate (2–256, defaults to 10 if out of range).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(
        f"[DHCP] Starting server | "
        f"mask={args.ip_mask}.0/24 | "
        f"pool={args.allocation} IPs | "
    )

    server = DHCPServer(
        ip_mask=args.ip_mask,
        allocation=args.allocation,
    )
    server.serve()


if __name__ == "__main__":
    main()
