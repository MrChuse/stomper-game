import queue
from dataclasses import dataclass, field

from core import Action
from utils import Connection

from traceback import print_exc

@dataclass
class ServerPacket:
    tick: int
    actions: dict[int, list[Action]] = field(init=False)

    def __post_init__(self):
        self.actions = {}

    def to_list(self):
        res = [self.tick, len(self.actions)]
        for player, actions in self.actions.items():
            res.append(player)
            res.append(len(actions))
            for a in actions:
                res.append(a.value)
        return res


class Server(Connection):
    def __init__(self, host='', port=50007):
        super().__init__(host, port)
        self.clients = []
        self.on_connect_callbacks = []
        self.on_disconnect_callbacks = []

    def sendall(self, data):
        for c in self.clients:
            if c == 'local': continue
            self.send(data, c)

    def quit(self):
        print("quit initialized")
        self.sendall(b'exit')
        super().quit()
        print("quit success")

    def loop(self):
        self.sock.bind((self.host, self.port))

        while self.alive:
            try:
                data, addr = self.recv()
            except TimeoutError:
                pass
            else:
                try:
                    if data == b'connect':
                        self.clients.append(addr)
                        self.sendstr('OK', addr)
                        
                        for f in self.on_connect_callbacks:
                            f()

                        # self.actions_to_remote.put({'player': len(self.clients), 'action': Action.CONNECT})
                        print(f'Client {addr} connected')
                    elif data == b'exit':
                        for f in self.on_disconnect_callbacks:
                            f(self.clients.index(addr))
                        self.packets_to_remote.put({'player': self.clients.index(addr), 'action': Action.DISCONNECT}) # bad
                        self.clients.remove(addr)
                        print('Client', addr, 'disconnected')
                    else:
                        try:
                            try:
                                player = self.clients.index(addr)
                            except ValueError:
                                print(f"This player is not found: {addr}")
                                continue
                            data = list(map(int, data.decode().split()))
                            # # if data[0] == len(data) - 1:
                            #     tick = data[1]
                            #     actions = list(map(Action, data[2:]))
                            tick = data[0]
                            actions = list(map(Action, data[1:]))
                            packet = ServerPacket(tick)
                            packet.actions[player] = actions
                            self.packets_to_local.put(packet)
                            # print('received', tick)
                            # else:
                            #     print(f'ACHTUNG! len data was wrong: {data[0]} != {len(data)}-1')
                        except Exception as e:
                            print("Exception...", e, data)
                            print_exc()
                except queue.ShutDown:
                    return

            try:
                packet = self.packets_to_remote.get(False)
            except queue.ShutDown:
                return
            except queue.Empty:
                pass
            else:
                for addr in self.clients:
                    if addr == 'local': continue
                    if isinstance(packet, dict) and 'state' in packet:
                        self.send(packet['state'], addr)
                    else:
                        # print('sent', packet.tick)
                        self.sendlistint(packet.to_list(), addr)
