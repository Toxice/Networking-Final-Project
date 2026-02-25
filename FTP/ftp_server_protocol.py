# ftp_server_protocol.py

def service_ready(self):
    return {"response": "service ready"}

def file_okay(byte_size):
    return {"response": "file okay",
            "byte_size": byte_size}

def closing_data():
    return {"response": "closing data"}

def service_teardown():
    return {"response": "service teardown"}

def file_unavailable():
    return {"response": "file unavailable"}