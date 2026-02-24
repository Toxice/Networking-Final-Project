import socket, json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

request = {"url": "www.example.com"}
sock.sendto(json.dumps(request).encode(), ("127.0.0.1", 9000))

data, _ = sock.recvfrom(4096)
print(data.decode())