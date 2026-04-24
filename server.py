import queue

from core import Action
from utils import Connection

class Server(Connection):
    def __init__(self, host='', port=50007):
        super().__init__(host, port)
        self.clients = []

    def quit(self):
        print("quit initialized")
        for c in self.clients:
            if c == 'local': continue
            self.sock.sendto(b'exit', c)
        super().quit()
        print("quit success")

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
                        self.actions_to_remote.put({'player': self.clients.index(addr), 'action': Action.DISCONNECT}) # bad
                        self.clients.remove(addr)
                        print('Client', addr, 'disconnected')
                    else:
                        try:
                            action = int(data.decode('utf-8'))
                            action = {'player': self.clients.index(addr), 'action': Action(action)}
                            print('Added', action)
                            self.actions_to_local.put(action)
                            self.actions_to_remote.put(action) # bad
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
                    if addr == 'local': continue
                    if 'state' in action:
                        self.sock.sendto(action['state'], addr)
                    else:
                        l = map(str, (action['player'], action['action'].value, *action.get('params', [])))
                        self.sock.sendto(' '.join(l).encode('utf-8'), addr)
