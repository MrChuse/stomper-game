import queue

from utils import Connection
from core import Action

class Client(Connection):
    def quit(self):
        print('quit initialized')
        self.sendstr('exit')
        super().quit()
        print('quit success')

    def loop(self):
        self.sendstr('connect')
        for i in range(10):
            try:
                res = self.recvstr()
                break
            except ConnectionResetError:
                print('Cant find the server')
            except TimeoutError:
                print('Timeout')
        else:
            return
        if res == 'OK':
            print('Connection established')

        while self.alive:
            try:
                data = self.recvstr()
            except TimeoutError:
                pass
            else:
                if data == 'exit': 
                    self.quit()
                    break
                try:
                    cmd_or_player, *params = data.split(' ')
                    if cmd_or_player == 'state':
                        self.actions_to_local.put({'state': params})
                    else:
                        player = int(cmd_or_player)
                        params = list(map(int, params))
                        self.actions_to_local.put({'player': player, 'action': Action(params[0]), 'params': params[1:]})
                except Exception as e:
                    print("Exception...", e, data)

            try:
                action = self.actions_to_remote.get(False)
            except queue.ShutDown:
                return
            except queue.Empty:
                pass
            else:
                self.sendstr(str(action.value))
