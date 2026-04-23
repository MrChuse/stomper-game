import pygame
import pygame.draw


# Echo client program
import socket

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

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True

x = 100
y = 100
size = 30

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        x -= 1
    if keys[pygame.K_RIGHT]:
        x += 1
    if keys[pygame.K_UP]:
        y -= 1
    if keys[pygame.K_DOWN]:
        y += 1

    screen.fill('black')

    pygame.draw.rect(screen, 'red', (x,y,size,size))

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()