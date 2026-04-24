import threading
from queue import Queue
import socket

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args)
        self.start()

class Connection:
    def __init__(self):
        self.host = 'localhost' # The remote host
        self.port = 50007       # The same port as used by the server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1/60)

        # threading
        self.alive = True
        self.thread = Thread(self.loop)

        # game related stuff
        self.actions_to_local = Queue()
        self.actions_to_remote = Queue()

    def quit(self):
        self.alive = False
        self.actions_to_local.shutdown()
        self.actions_to_remote.shutdown()
        self.thread.join()

    def send(self, data: bytes):
        print('Send:', data, '->', (self.host, self.port))
        self.sock.sendto(data, (self.host, self.port))

    def sendstr(self, s: str):
        self.send(s.encode('utf-8'))

    def recv(self):
        data, addr = self.sock.recvfrom(1024)
        print('Recv', data, '<-', addr)
        return data

    def recvstr(self):
        data = self.recv()
        return data.decode('utf-8')
    
    def loop(self):
        pass
