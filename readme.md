# Networking Final Project - FTP Server

In This Project we've implemented a simple **FTP Server over TCP/RUDP** using JSON based protocols
We've Also implemented a Bitwise DNS Server and a DHCP Server
---

# Assignment Architecture:

---

# Components:

---

## - **DNS Server (`server.py`)**

---

## - **Client (`client.py`)**

---

## - **DHCP Server (`proxy.py`)**
   ### Server's flow is according to the DORA process (Discover → Offer → Request → Acknowledge)
   ### a generic request may look as:
```
{
 "message_type": "DISCOVER",
 "transaction_id": 3687,
 "client_mac": 00-1A-2B-3C-4D-5E
     } 
```

#### and of course the response:
```
{
 "message_type": "ACK",
 "transaction_id": 3687,
 "ip_address": 192.168.1.15,
 "dns_server": 104.26.10.226
      }
```

---

- **FTP Server**

---

