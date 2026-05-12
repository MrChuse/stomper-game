import threading
from queue import Queue
import socket
import logging
from uuid import UUID


logger = logging.getLogger(__name__)
logger_send = logging.getLogger(f'{__name__}.send')
logger_recv = logging.getLogger(f'{__name__}.recv')

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args, name=self.__class__.__name__)
        self.start()

class Connection:
    def __init__(self, host='', port=50007):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1/30)

        # threading
        self.alive = True
        self.thread = Thread(self.loop)

        # game related stuff
        self.packets_to_local = Queue()
        self.packets_to_remote = Queue()

    def quit(self):
        self.alive = False
        self.packets_to_local.shutdown()
        self.packets_to_remote.shutdown()

    def send(self, data: bytes, addr=None):
        if addr is None:
            addr = (self.host, self.port)
        logger_send.debug(f'Send: {data} -> {addr}')
        if len(data) > 1500:
            raise ValueError(f"Tried to send data with len {len(data)}. Max is 1500.")
        self.sock.sendto(data, addr)

    def sendstr(self, s: str, addr=None):
        self.send(s.encode('utf-8'), addr)
    
    def sendlistint(self, l: list[int], addr=None):
        s = ' '.join(map(str, l))
        self.sendstr(s, addr)

    def recv(self):
        data, addr = self.sock.recvfrom(1500)
        logger_recv.debug(f'Recv {data} <- {addr}')
        return data, addr

    def recvstr(self):
        data, addr = self.recv()
        return data.decode('utf-8'), addr

    def loop(self):
        pass

def is_valid_uuid(uuid: str, version=4):
    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid
