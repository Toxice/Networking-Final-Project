class IP:
    def __init__(self, ip:str, lease_time:int, in_use:bool):
        self.ip = ip
        self.lease_time = lease_time
        self.in_use = in_use