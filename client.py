import queue
from dataclasses import dataclass, field
import logging

from utils import Connection
from back.core import Action

from server import ServerPacket # avoiding circular imports

@dataclass()
class ClientPacket:
    tick: int
    actions: list[Action] = field(init=False)

    def __post_init__(self):
        self.actions = []

    def to_list(self):
        res = [self.tick]
        for action in self.actions:
            res.append(action.value)
        return res

class Client(Connection):
    def quit(self):
        logging.info('quit initialized')
        self.sendstr('exit')
        super().quit()
        logging.info('quit success')

    def loop(self):
        self.sendstr('connect')
        for i in range(10):
            try:
                res, addr = self.recv()
                res = res.decode('utf-8')
                break
            except ConnectionResetError:
                logging.error('Cant find the server')
            except TimeoutError:
                logging.error('Timeout')
            except UnicodeDecodeError:
                logging.error(f'Received trash: {res}')
        else:
            return
        if res == 'OK':
            logging.info('Connection established')

        while self.alive:
            try:
                data, addr = self.recvstr()
            except TimeoutError:
                pass
            else:
                if data == 'exit':
                    self.quit()
                    break
                try:
                    state_or_tick, *data = data.split(' ')
                    if state_or_tick == 'state':
                        self.packets_to_local.put({'state': data})
                    else:
                        packet = ServerPacket(int(state_or_tick))
                        data = list(map(int, data))
                        it = iter(data)
                        try:
                            num_players = next(it)
                            for i in range(num_players):
                                player = next(it)
                                length = next(it)
                                actions = []
                                for i in range(length):
                                    a = next(it)
                                    actions.append(Action(a))
                                packet.actions[player] = actions
                        except StopIteration as e:
                            logging.error(f'ServerPacket parsing went wrong: {e}, {data}')
                            continue
                        try:
                            next(it)
                        except StopIteration as e:
                            pass # data should be exhausted by now
                        else:
                            logging.error(f'More data was present than needed to parse ServerPacket... IDK {data}')
                        
                        self.packets_to_local.put(packet)
                        logging.debug(f'received {state_or_tick}')
                except Exception as e:
                    logging.error("Exception...", e, data)

            try:
                packet: ClientPacket = self.packets_to_remote.get(False)
            except queue.ShutDown:
                return
            except queue.Empty:
                pass
            else:
                logging.debug(f'sent {packet.tick}')
                self.sendlistint(packet.to_list())
