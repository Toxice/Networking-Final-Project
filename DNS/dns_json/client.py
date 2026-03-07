import socket, json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

request = {"url": "pornhub.com"}
request2 = {"url": "www.github.com", "ip": "3.4.5.7"}
sock.sendto(json.dumps(request2).encode(), ("127.0.0.1", 9000))

data, _ = sock.recvfrom(4096)
print(data.decode())