import socket, json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

request = {"url": "   PoRnH uB.CoM.   "}
request2 = {"url": "   test.com   ", "ip": "5.6.7.8"}
sock.sendto(json.dumps(request).encode(), ("127.0.0.1", 9000))
print("Connected to the server... ")

data, _ = sock.recvfrom(4096)
print(data.decode())