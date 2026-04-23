from main import Game, Artist
from client import Client

class GameClientArtist:
    def __init__(self) -> None:
        self.artist = Artist()
        self.connection = Client()
        self.game = Game()