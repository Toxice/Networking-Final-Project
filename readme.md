### Networking Project - Liza Bahak | Nicko Korgan | Mor Romano

* This Project consists of 3 Parts:
* Custom FTP Server
* DHCP Server
* DNS Server
---
## Architecture & Components:

---

### DNS Server:
* `dns_protocol.py` - struct packing & unpacking and DNS methods
* `dns_server.py` - actual DNS server
---

### DHCP Server:
* `dhcp_model.py` - python dataclass, used as a base for abstraction in the byte to class process
* `dhcp_protocol.py` - used for all struct packing & unpacking, all DHCP methods are based here
* `dhcp_server.py` - actual DHCP server
---

### FTP Server:
* `ftp_server.py` - FTP Server class

### since FTP is basically a text based application protocol, there is no need to a fancy 3 class based architecture, one class is enough

---

### Client:
* `ftp_client.py` - unified client, made to work with DHCP, DNS and FTP Servers

