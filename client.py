import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)
sock.sendto("guts gonna be proud of you".encode(),("127.0.0.1",8053))
try:
    data, addr = sock.recvfrom(1024)
    print(data.decode())
    print(f"from: {addr}")
except socket.timeout:
    print("Connection timed out")
    sock.close()
except Exception as e:
    print(e)



