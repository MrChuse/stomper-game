import queue
from dataclasses import dataclass, field
import logging
import uuid
from collections.abc import Iterator

from utils import Connection
from back.core import Action

from server import ServerTickActions

@dataclass
class ClientTickActions:
    tick: int
    actions: list[Action] = field(init=False)

    def __post_init__(self):
        self.actions = []

    def to_list(self):
        res = [self.tick, len(self.actions)]
        for action in self.actions:
            res.append(action.value)
        return res

@dataclass
class ClientPacket:
    tick_actions: list[ClientTickActions]

    def to_list(self):
        res = [len(self.tick_actions)]
        for ta in self.tick_actions:
            l = ta.to_list()
            res.extend(l)
        return res

class Client(Connection):
    def __init__(self, host='', port=50007):
        self.uuid = uuid.uuid4()
        super().__init__(host, port)
        self.on_disconnect_callbacks = []

    def quit(self):
        logging.info('quit initialized')
        self.sendstr('exit')
        super().quit()
        logging.info('quit success')

    def parse_player_actions(self, it):
        player = next(it)
        length = next(it)
        actions = []
        for i in range(length):
            a = next(it)
            actions.append(Action(a))
        return player, actions

    def parse_server_tick_actions(self, it: Iterator):
        tick = next(it)
        packet = ServerTickActions(tick)
        num_players = next(it)
        for i in range(num_players):
            player, actions = self.parse_player_actions(it)
            packet.actions[player] = actions
        return packet

    def loop(self):
        self.sendstr(f'connect {self.uuid}')
        for i in range(200):
            try:
                res, addr = self.recv()
                res = res.decode('utf-8')
                break
            except ConnectionResetError:
                logging.error('Cant find the server')
            except TimeoutError:
                logging.error('Timeout')
            except UnicodeDecodeError:
                logging.error(f'Received trash')
        else:
            return
        if res.startswith('OK'):
            ok, num = res.split()
            logging.info(f'Connection established. Player number {num}')
            self.packets_to_local.put({'player_id': int(num)})

        while self.alive:
            try:
                data, addr = self.recvstr()
            except TimeoutError:
                pass
            except UnicodeDecodeError:
                logging.error(f'Received trash')
            else:
                if data == 'exit':
                    self.quit()
                    break
                try:
                    state_or_tick, *data = data.split(' ')
                    if state_or_tick == 'state':
                        self.packets_to_local.put({'state': data})
                    elif state_or_tick == 'disconnect':
                        player = int(data[0])
                        for f in self.on_disconnect_callbacks:
                            f(player)

                    else:
                        length = int(state_or_tick)
                        data = list(map(int, data))
                        it = iter(data)

                        parsed_packets = []
                        try:
                            for i in range(length):
                                packet = self.parse_server_tick_actions(it)
                                parsed_packets.append(packet)
                        except StopIteration as e:
                            logging.error(f'ServerPacket parsing went wrong: {e}, {data}')
                            continue
                        try:
                            next(it)
                        except StopIteration as e:
                            pass # good case
                        else:
                            logging.error(f'More data was present than needed to parse ServerPacket... IDK {data}')

                        # parsing complete and successful
                        for packet in parsed_packets:
                            self.packets_to_local.put(packet)
                        logging.debug(f'received {state_or_tick}')
                except Exception as e:
                    logging.error(f"Exception..., {e}, {data}")

            try:
                packet: ClientPacket = self.packets_to_remote.get(False)
            except queue.ShutDown:
                return
            except queue.Empty:
                pass
            else:
                logging.debug(f'sent {packet}')
                self.sendlistint(packet.to_list())
