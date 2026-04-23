import socket
import queue
from queue import Queue

from utils import Thread
from main import Game

class Client():
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
    
    def add_actions(self, actions):
        for a in actions:
            self.actions_to_local.put({'player': 0, 'action': a})
            self.actions_to_remote.put({'player': 0, 'action': a})
    
    def quit(self):
        print('quit initialized')
        self.sendstr('exit')
        self.alive = False
        self.actions_to_local.shutdown()
        self.actions_to_remote.shutdown()
        self.thread.join()
        print('quit success')

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
        self.sendstr('connect')
        try:
            res = self.recvstr()
        except ConnectionResetError:
            print('Cant find the server')
            return
        if res == 'OK':
            print('Connection established')
        
        while self.alive:
            try:
                action = self.actions_to_remote.get()
            except queue.ShutDown:
                return
            self.sendstr(str(action['action'].value))
            try:
                data = self.recvstr()
            except TimeoutError:
                continue
            if data == 'exit': break
            

c = Client()
game = Game(c)
Thread(game.main)