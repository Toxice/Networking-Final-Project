import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

def load_json(filename):
    """Helper function to read any JSON file safely."""
    path = os.path.join(BASE_DIR, filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Using empty settings.")
        return {}

# --- Load all JSON files here ---
dhcp_data = load_json("dhcp.json")
dns_database = load_json("dns.json")

# --- Export specific variables for your modules to use ---
# Database Module Settings
DNS_IP = dhcp_data.get("dns_ip", "127.0.0.1")
DNS_DATABASE = dns_database.get("data_base")