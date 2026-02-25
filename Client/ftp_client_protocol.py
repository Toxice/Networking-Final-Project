# ftp_client_protocol.py

def retrieve(filename):
    return {"command": "RETR",
            "file": filename}

def quit():
    return {"command": "QUIT"}