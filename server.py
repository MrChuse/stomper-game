import socket

from main import Game, Action
from utils import Thread

class Server:
    def __init__(self):
        self.host = ''    # Symbolic name meaning all available interfaces
        self.port = 50007 # Arbitrary non-privileged port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1/60)

        # server
        self.clients = []

        # threading
        self.alive = True
        self.thread = Thread(self.loop)

        # game related stuff
        self.actions = []


    def add_actions(self, actions):
        for a in actions:
            self.actions.append({'player': 0, 'action': a})

    def get_all_actions(self):
        return self.actions

    def quit(self):
        print("quit initialized")
        for c in self.clients:
            self.sock.sendto(b'exit', c)
        self.alive = False
        self.thread.join()
        print("quit success")

    def send(self, data: bytes):
        self.sock.sendto(data, (self.host, self.port))

    def sendstr(self, s: str):
        self.send(s.encode('utf-8'))

    def recv(self):
        data, addr = self.sock.recvfrom(1024)
        return data

    def recvstr(self):
        data = self.recv()
        return data.decode('utf-8')

    def loop(self):        
        self.sock.bind((self.host, self.port))

        while self.alive:
            self.actions = []
            try:
                data, addr = self.sock.recvfrom(1024)
            except TimeoutError:
                continue

            if data == b'connect':
                self.clients.append(addr)
                self.sock.sendto('OK'.encode('utf-8'), addr)
                self.actions.append({'player': len(self.clients), 'action': Action.CONNECT})
                print(f'Client {addr} connected')
            elif data == b'exit':
                self.clients.remove(addr)
                print('Client', addr, 'disconnected')
            else:
                print('Received', addr, data)
                if data == b'exit': break
                self.sock.sendto(data, addr)
            

s = Server()
game = Game(s)
draw_thread = Thread(game.main)