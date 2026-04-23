import socket

import pygame
import pygame.draw

from utils import Thread
from main import main

def client():
    HOST = 'localhost'    # The remote host
    PORT = 50007          # The same port as used by the server
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        msg = input()
        while msg != 'exit':
            s.sendto(msg.encode('utf-8'), (HOST, PORT))
            data, addr = s.recvfrom(1024)
            print('Received', repr(data))
            msg = input()
        s.sendto(msg.encode('utf-8'), (HOST, PORT))

Thread(client)
Thread(main)