import queue
from dataclasses import dataclass, field
import logging
from collections.abc import Iterator
from itertools import islice

from back.core import Action
from utils import Connection, Thread, is_valid_uuid

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

    def parse_tick_actions(self, it: Iterator, player: int):
        tick = next(it)
        length = next(it)
        actions = list(map(Action, islice(it, length)))
        packet = ServerPacket(tick)
        packet.actions[player] = actions
        return packet

    def loop(self):
        self.sock.bind((self.host, self.port))

        while self.alive:
            try:
                data, addr = self.recv()
            except TimeoutError:
                pass
            else:
                    if addr not in self.clients:
                        try:
                            data = data.decode()
                        except UnicodeDecodeError as e:
                            logging.error(e)
                        if data.startswith('connect'):
                            clients_uuid = data.split(' ')[-1]
                            if is_valid_uuid(clients_uuid):
                                s = f'OK {len(self.clients)}'
                                self.clients.append(addr)
                                self.sendstr(s, addr)
                                for f in self.on_connect_callbacks:
                                    f()
                                logging.info(f'Client {addr} connected')
                            else:
                                s = "418 I'm a teapot"
                                self.sendstr(s, addr)
                                logging.info(f'{addr} tried to connect with {data}')
                    else:
                        if data == b'exit':
                            if addr in self.clients:
                                for f in self.on_disconnect_callbacks:
                                    f(self.clients.index(addr))
                                try:
                                    self.packets_to_remote.put({'disconnected_player': self.clients.index(addr)}) # bad
                                except queue.ShutDown:
                                    return
                                self.clients.remove(addr)
                                print('Client', addr, 'disconnected')
                        else:
                            try:
                                player = self.clients.index(addr)
                                data = list(map(int, data.decode().split()))
                                it = iter(data)

                                try:
                                    received_ticks = []
                                    length = next(it)
                                    for i in range(length):
                                        packet = self.parse_tick_actions(it, player)
                                        try:
                                            self.packets_to_local.put(packet)
                                        except queue.ShutDown:
                                            return
                                        received_ticks.append(packet.tick)
                                    logging.debug(f'received {received_ticks}')
                                except StopIteration:
                                    logging.error("Couldnt parse tick actions")
                                try:
                                    next(it)
                                except StopIteration:
                                    pass # good case
                                else:
                                    logging.error("Somehow more data was present than needed to parse tick actions")
                            except Exception as e:
                                logging.error(f"Exception... {e}, {data}")
                                print_exc()
