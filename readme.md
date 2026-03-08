### Networking Project

[![Contributor](https://img.shields.io/badge/Contributor-Liza_Bahak-green)](https://github.com/LizPlzArt) [![Contributor](https://img.shields.io/badge/Contributor-Nicko_Korgan-green)](https://github.com/jaoniko18) [![Contributor](https://img.shields.io/badge/Contributor-Mor_Romano-green)](https://github.com/Toxice) 

[![Trello](https://shields.io/badge/Project_Track-Trello-purple?logo=Trello&style=flat)](https://trello.com/b/KPWm4q41/network-final-assignment)

### This Project consists of 3 Parts:
* Custom FTP Server
* DHCP Server
* DNS Server
---
## Architecture & Components:


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

### Bibliography:
[![Google Docs](https://img.shields.io/badge/DHCP-RFC2121-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://www.ietf.org/rfc/rfc2131.txt)
[![Google Docs](https://img.shields.io/badge/DNS-RFC1035-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://www.ietf.org/rfc/rfc1035.txt)
[![Google Docs](https://img.shields.io/badge/FTP-RFC959-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://www.ietf.org/rfc/rfc959.txt)