import threading
from queue import Queue
import socket
import logging

logger = logging.getLogger(__name__)

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args, name=self.__class__.__name__)
        self.start()

class Connection:
    def __init__(self, host='', port=50007):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1/1000)

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
        self.thread.join()

    def send(self, data: bytes, addr=None):
        logger.debug(f'Send: {data} -> {addr}')
        if addr is None:
            addr = (self.host, self.port)
        self.sock.sendto(data, addr)

    def sendstr(self, s: str, addr=None):
        self.send(s.encode('utf-8'), addr)
    
    def sendlistint(self, l: list[int], addr=None):
        s = ' '.join(map(str, l))
        self.sendstr(s, addr)

    def recv(self):
        data, addr = self.sock.recvfrom(1024)
        logger.debug(f'Recv {data} <- {addr}')
        return data, addr

    def recvstr(self):
        data, addr = self.recv()
        return data.decode('utf-8'), addr

    def loop(self):
        pass
