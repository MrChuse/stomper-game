import queue
from dataclasses import dataclass, field
import logging

from back.core import Action
from utils import Connection, Thread

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
        self.send_thread = Thread(self.send_loop)

    def sendall(self, data):
        for c in self.clients:
            if c == 'local': continue
            self.send(data, c)

    def quit(self):
        print("quit initialized")
        self.sendall(b'exit')
        super().quit()
        print("quit success")

    def send_loop(self):
        while self.alive:
            try:
                packet = self.packets_to_remote.get()
            except queue.ShutDown:
                return
            except queue.Empty:
                logging.error("Empty packets to remote: should be unreachable")
                pass
            else:
                for addr in self.clients:
                    if addr == 'local': continue
                    if isinstance(packet, dict):
                        if 'state' in packet:
                            logging.debug(f'sent state {packet['state']}')
                            self.send(packet['state'], addr)
                        elif 'disconnected_player' in packet:
                            self.sendstr(f'disconnect {packet["disconnected_player"]}', addr)
                        else:
                            raise ValueError(f'I dont understand this packet: {packet}')
                    elif isinstance(packet, ServerPacket):
                        logging.debug(f'sent {packet.tick}')
                        self.sendlistint(packet.to_list(), addr)
                    else:
                        logging.debug(f'unsupported type: {type(packet)} {packet}')

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
                        s = f'OK {len(self.clients)}'
                        self.clients.append(addr)
                        self.sendstr(s, addr)
                        
                        for f in self.on_connect_callbacks:
                            f()

                        # self.actions_to_remote.put({'player': len(self.clients), 'action': Action.CONNECT})
                        print(f'Client {addr} connected')
                    elif data == b'exit':
                        if addr in self.clients:
                            for f in self.on_disconnect_callbacks:
                                f(self.clients.index(addr))
                            self.packets_to_remote.put({'disconnected_player': self.clients.index(addr)}) # bad
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
                            logging.debug(f'received {tick}')
                            # else:
                            #     print(f'ACHTUNG! len data was wrong: {data[0]} != {len(data)}-1')
                        except Exception as e:
                            print("Exception...", e, data)
                            print_exc()
                except queue.ShutDown:
                    return
