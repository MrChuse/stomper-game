import settings
if settings.PROFILER:
    import yappi

import socket
import logging

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UITextEntryLine
from pygame_gui.windows import UIMessageWindow

from game_client_artist import GameClientArtist
from game_server_artist import GameServerArtist
from game_artist import GameArtist

class Screen:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.window_size = self.surface.get_rect().size
        self.background = pygame.Surface(self.window_size)
        self.background_color = '#101010'
        self.background.fill(pygame.Color(self.background_color))
        self.return_value = None
        self.force_quit = False
        self.manager = pygame_gui.UIManager(self.window_size)
        self.framerate = 60

    def clean_up(self):
        return
    
    def process_events(self, event):
        return self.manager.process_events(event)
    
    def update(self, time_delta):
        self.manager.update(time_delta)
        self.manager.draw_ui(self.surface)

    def on_window_size_changed(self, size):
        self.window_size = size
        self.manager.set_window_resolution(size)
        self.background = pygame.Surface(size)
        self.background.fill(pygame.Color(self.background_color))

    def main(self):
        clock = pygame.time.Clock()
        self.is_running = True
        while self.is_running:
            time_delta = clock.tick(self.framerate)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.force_quit = True
                    self.is_running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.force_quit = True
                        self.is_running = False
                elif event.type == pygame.WINDOWSIZECHANGED:
                    if event.window is None:
                        self.on_window_size_changed((event.x, event.y))
                self.process_events(event)
            self.surface.blit(self.background, (0, 0))
            
            self.update(time_delta)
            
            pygame.display.set_caption(f'Stomper Game | {clock.get_fps():.1f}')
            pygame.display.update()
        self.clean_up()
        return self.return_value

class LocalOnlinePickerScreen(Screen):
    def __init__(self, surface: pygame.Surface):
        super().__init__(surface)
        self.manager = pygame_gui.UIManager(surface.get_rect().size)
        rect1 = pygame.Rect(surface.get_rect())
        rect1 = rect1.inflate(-200, -200)
        rect1.height /= 2
        self.local_button = UIButton(rect1, 'Local', manager=self.manager,)
        rect2 = pygame.Rect((0, 0), rect1.size)
        # rect2.bottomright = -100, -100
        self.online_button = UIButton(rect2, 'Online', manager=self.manager,
                                      anchors={'centerx': 'centerx',
                                            'top_target': self.local_button})
        rect3 = pygame.Rect(rect2)
        rect3.left = rect1.left
        rect3.width /= 2
        self.host_button = UIButton(rect3, 'Host', self.manager, visible=False,
                                    anchors={'top_target': self.local_button})
        rect4 = pygame.Rect(rect3)
        rect4.left = 0
        rect4.height -= 30
        self.client_button = UIButton(rect4, 'Connect', self.manager, visible=False,
                                    anchors={'top_target': self.local_button,
                                            'left_target':self.host_button})
        self.placeholder_ip = '127.0.0.1'
        self.client_text_entry = UITextEntryLine(pygame.Rect(0, 0, rect4.width, 30), self.manager,
                                                 visible=False, placeholder_text=self.placeholder_ip,
                                                 anchors={'top_target': self.client_button,
                                                          'left_target':self.host_button})

    def process_events(self, event):
        super().process_events(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.local_button:
                self.return_value = 'local'
                self.is_running = False
            elif event.ui_element == self.online_button:
                self.online_button.hide()
                self.host_button.show()
                self.client_button.show()
                self.client_text_entry.show()
            elif event.ui_element == self.host_button:
                self.return_value = 'online host'
                self.is_running = False
            elif event.ui_element == self.client_button:
                text = self.client_text_entry.text
                if not text:
                    text = self.placeholder_ip
                try:
                    socket.inet_aton(text)
                except socket.error as e:
                    rect = pygame.Rect(self.surface.get_rect())
                    rect = rect.scale_by(0.5, 0.5)
                    UIMessageWindow(rect, f'{text} is an invalid IPv4 address')
                else:
                    self.return_value = f'online client {text}'
                    self.is_running = False

def main():
    pygame.init()
    pygame.display.set_caption('Stomper Game')
    window_surface = pygame.display.set_mode((480, 360))

    lop = LocalOnlinePickerScreen(window_surface)
    res = lop.main()
    if lop.force_quit:
        return

    if res.startswith('local'):
        instance = GameArtist(window_surface)
    elif res.startswith('online'):
        # online host
        # or
        # online client IP
        # IP is passed to GameClientArtist
        parts = res.split()
        if len(parts) == 2 and parts[1] == 'host':
            instance = GameServerArtist(screen=window_surface)
        elif len(parts) == 3 and parts[1] == 'client':
            instance = GameClientArtist(parts[2], screen=window_surface)
    pygame.quit()

if __name__ == '__main__':
    if settings.PROFILER:
        yappi.start()
    logging.basicConfig(level=settings.LOGGING_LEVEL)
    main()
    if settings.PROFILER:
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()