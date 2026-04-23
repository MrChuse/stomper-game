import socket

import pygame
import pygame.draw

from main import main
from utils import Thread

def serve():
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 50007              # Arbitrary non-privileged port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        while True:
            data, addr = s.recvfrom(1024)
            print('Received', addr, data)
            if data == b'exit': break
            s.sendto(data, addr)

server_thread = Thread(serve)
draw_thread = Thread(main)