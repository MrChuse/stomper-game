import socket
import queue
from queue import Queue

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
        self.actions_to_local = Queue()
        self.actions_to_remote = Queue()


    def add_actions(self, actions):
        for a in actions:
        #     self.actions_to_local.put({'player': 0, 'action': a})
            self.actions_to_remote.put(a)

    def quit(self):
        print("quit initialized")
        for c in self.clients:
            self.sock.sendto(b'exit', c)
        if self.alive:
            self.alive = False
            self.actions_to_local.shutdown()
            self.actions_to_remote.shutdown()
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
            try:
                data, addr = self.sock.recvfrom(1024)
            except TimeoutError:
                pass
            else:
                try:
                    if data == b'connect':
                        self.clients.append(addr)
                        self.sock.sendto('OK'.encode('utf-8'), addr)
                        self.actions_to_local.put({'player': len(self.clients), 'action': Action.CONNECT})
                        # self.actions_to_remote.put({'player': len(self.clients), 'action': Action.CONNECT})
                        print(f'Client {addr} connected')
                    elif data == b'exit':
                        self.actions_to_local.put({'player': self.clients.index(addr), 'action': Action.DISCONNECT})
                        self.actions_to_remote.put({'player': self.clients.index(addr), 'action': Action.DISCONNECT})
                        self.clients.remove(addr)
                        print('Client', addr, 'disconnected')
                    else:
                        try:
                            action = int(data.decode('utf-8'))
                            action = {'player': self.clients.index(addr), 'action': Action(action)}
                            print('Added', action)
                            self.actions_to_local.put(action)
                            self.actions_to_remote.put(action)
                        except Exception as e:
                            print("Exception...", e, data)
                except queue.ShutDown:
                    return
            
            try:
                action = self.actions_to_remote.get(False)
            except queue.ShutDown:
                return
            except queue.Empty:
                pass
            else:
                for addr in self.clients:
                    print(action)
                    l = map(str, (action['player'], action['action'].value, *action.get('params', [])))
                    self.sock.sendto(' '.join(l).encode('utf-8'), addr)



s = Server()
game = Game(s)
try:
    game.main()
except KeyboardInterrupt:
    game.quit()
