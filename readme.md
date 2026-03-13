# Networking Project

[![Contributor](https://img.shields.io/badge/Contributor-Liza_Bahak-green)](https://github.com/LizPlzArt) [![Contributor](https://img.shields.io/badge/Contributor-Nicko_Korgan-green)](https://github.com/jaoniko18) [![Contributor](https://img.shields.io/badge/Contributor-Mor_Romano-green)](https://github.com/Toxice) 

[![Trello](https://shields.io/badge/Project_Track-Trello-purple?logo=Trello&style=flat)](https://trello.com/b/KPWm4q41/network-final-assignment)

### This Project consists of 3 Parts and 1 Additional One:
* Custom FTP Server
* DHCP Server
* DNS Server
* Custom RUDP Protocol
---
## Architecture & Components:

---
### Project Tree:

```
Networking-Project
├── JSONClient
│   └── client.py
├── RFCClient
│   └── client.py
├── dhcp_bitwise
│   ├── dhcp.json
│   ├── dhcp_client.py
│   ├── dhcp_model.py
│   ├── dhcp_protocol.py
│   ├── dhcp_server.py
│   ├── dhcp_service.py
│   └── example_client.py
├── dhcp_json
│   ├── dhcp.json
│   ├── dhcp_protocol.py
│   ├── dhcp_server.py
│   ├── dhcp_service.py
│   └── json_config.py
├── DNS
│   ├── DNS_binary
│   │   ├── dns.json
│   │   ├── dns_protocol.py
│   │   ├── dns_server.py
│   │   └── dns_service.py
│   └── dns_json
│       ├── client.py
│       ├── dns.json
│       ├── dns_protocol.py
│       ├── dns_server.py
│       └── dns_service.py
├── FTP
│   ├── server_files/
│   ├── __init__.py
│   ├── ftp_server.py
│   └── ftp_service.py
├── RUDP
│   ├── __init__.py
│   ├── rudp_protocol.py
│   ├── rudp_server.py
│   └── rudp_service.py
└── Dissectors
    ├── Custom FTP
    │   └── fojp.lua
    ├── Custom RUDP
    │   └── crudp.lua
    ├── JSON DHCP
    │   └── json_dhcp.lua
    └── JSON_DNS
        └── dns_json.lua                               
```

### RFC DNS Server:
* works over port 8053, meant to not interfere with port 53
* `dns_protocol.py` - struct packing & unpacking and DNS methods
* `dns_server.py` - actual DNS server
---

### RFC DHCP Server:
+ works over ports 6767 and 6868, meant to not interfere with ports 67 and 68
* `dhcp_model.py` - python dataclass, used as  an abstraction layer from the bits representation to a class
* `dhcp_protocol.py` - used for struct packing & unpacking and all DHCP DORA process methods
* `dhcp_server.py` - the actual DHCP server
---

### JSON DNS Server:
* works over port 8053, meant to not interfere with port 53
* `dns_protocol.py` - 
* `dns_server.py` - 
---

### JSON DHCP Server:
+ works over ports 6767 and 6868, meant to not interfere with ports 67 and 68
* `dhcp_model.py` -
* `dhcp_protocol.py` - 
* `dhcp_server.py` - 
---

### FTP Server:
* works over port 2121 for Control (to not interfere with port 21), and a random port is selected for RUDP/TCP Data Channel
* `ftp_server.py` - FTP Server class

#### since FTP is basically a text based application protocol, there is no need to a fancy 3 class based architecture, one class is enough

---

### RUDP Server:
* based on the protocol assigned in Assignment 3
* `rudp_protocol.py` - contains the protocol functionality
* `rudp_server.py` - the RUDP Server, used for transferring data from the FTP Server to the Client
* `rudp_client.py` - the RUDP Client, used for transferring data from the FTP Client to the Server

---
### RFC Client:
* `client.py` - unified client, made to work with DHCP, DNS and FTP Servers
---

### JSON Client:
* `client.py` - unified client, made to work with DHCP, DNS and FTP Servers

---
### Dissectors:
* `crudp.lua` - Dissector for the Custom RUDP Protocol
* `fojp.lua` - Dissector for the Custom FTP Protocol (File Over JSON Protocol)
---

### Setup:
1. set the Lua dissectors inside Wireshark (in the plugins folder)
2. start each server:
* `python dhcp_server.py`
* `python dns_server.py`
* `python ftp_server.py`
3. run the client:
* `python client.py`

### Bibliography:
[![Google Docs](https://img.shields.io/badge/DHCP-RFC2121-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://www.ietf.org/rfc/rfc2131.txt)
[![Google Docs](https://img.shields.io/badge/DNS-RFC1035-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://www.ietf.org/rfc/rfc1035.txt)
[![Google Docs](https://img.shields.io/badge/FTP-RFC959-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://www.ietf.org/rfc/rfc959.txt)
