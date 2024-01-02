from collections.abc import Iterator
from dataclasses import dataclass
from itertools import batched

import pygame
from matplotlib.colors import CSS4_COLORS
from matplotlib.colors import rgb_to_hsv
from matplotlib.colors import to_rgb

from govee_remote.client import get_color
from govee_remote.client import GoveeClient


@dataclass
class State:
    color: str = "white"
    brightness: int = 100
    on: bool = True


class ButtonMap:
    def __init__(self) -> None:
        self._map: dict[str, pygame.Rect] = {}

    def register(self, key: str, rect: pygame.Rect) -> None:
        self._map[key] = rect

    def collisions(self, pos: tuple[int, int]) -> Iterator[str]:
        for key, rect in self._map.items():
            if rect.collidepoint(pos):
                yield key


def get_luma(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def redraw(screen: pygame.Surface, state: State) -> ButtonMap:
    button_map = ButtonMap()

    screen.fill("white")

    names = sorted(CSS4_COLORS, key=lambda c: tuple(rgb_to_hsv(to_rgb(c))))

    font = pygame.font.SysFont("Arial", 14)
    font_large = pygame.font.SysFont("Arial", 22, bold=1)

    on_color = "yellow" if state.on else "lightgray"
    on_rect = pygame.Rect(20, 30, 90, 45)
    button_map.register("power.on", on_rect)
    pygame.draw.rect(screen, get_color(on_color), on_rect)
    pygame.draw.rect(screen, get_color("black"), on_rect, width=2)
    on_text = font_large.render("On", True, "black")
    screen.blit(on_text, on_text.get_rect(center=on_rect.center))

    off_color = "lightgray" if state.on else "yellow"
    off_rect = pygame.Rect(150, 30, 90, 45)
    button_map.register("power.off", off_rect)
    pygame.draw.rect(screen, get_color(off_color), off_rect)
    pygame.draw.rect(screen, get_color("black"), off_rect, width=2)
    off_text = font_large.render("Off", True, "black")
    screen.blit(off_text, off_text.get_rect(center=off_rect.center))

    for col, batch in enumerate(batched(names, 20)):
        for row, name in enumerate(batch):
            rect = pygame.Rect(20 + col * 190, 100 + row * 40, 60, 30)
            pygame.draw.rect(screen, get_color(name), rect)
            pygame.draw.rect(screen, get_color("black"), rect, width=2)
            color_name = font.render(name.capitalize(), 1, "black")
            screen.blit(color_name, (20 + col * 190 + 70, 100 + row * 40 + 5))
            button_map.register(
                f"color.{name}", pygame.Rect(20 + col * 190, 100 + row * 40, 180, 30)
            )
            if name == state.color:
                color = "black" if get_luma(get_color(name)) > 130 else "white"
                checkmark = font_large.render("X", 1, color)
                screen.blit(checkmark, checkmark.get_rect(center=rect.center))

    row += 1

    brightness_label = font_large.render("Brightness", 1, "black")
    screen.blit(brightness_label, (20 + col * 190, 100 + row * 40 + 5))

    brightnesses = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    brightnesses.reverse()
    for row, brightness in enumerate(brightnesses, start=row + 1):
        rect = pygame.Rect(20 + col * 190, 100 + row * 40, 60, 30)
        pygame.draw.rect(
            screen, tuple(int(255 * brightness / 100) for _ in range(3)), rect
        )
        pygame.draw.rect(screen, get_color("black"), rect, width=2)
        color_name = font.render(f"{brightness}%", 1, "black")
        screen.blit(color_name, (20 + col * 190 + 70, 100 + row * 40 + 5))
        button_map.register(
            f"brightness.{brightness}",
            pygame.Rect(20 + col * 190, 100 + row * 40, 180, 30),
        )
        if brightness == state.brightness:
            color = "black" if brightness >= 50 else "white"
            checkmark = font_large.render("X", 1, color)
            screen.blit(checkmark, checkmark.get_rect(center=rect.center))

    pygame.display.flip()

    return button_map


def main(client: GoveeClient) -> None:
    pygame.init()
    pygame.display.set_caption("Govee Control Panel")
    client.on()
    state = State()
    client.color(state.color)
    client.brightness(state.brightness)
    screen = pygame.display.set_mode((1600, 900))
    clock = pygame.time.Clock()
    running = True

    button_map = redraw(screen, state)

    while running:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.MOUSEBUTTONUP:
                    pos = event.pos
                    for name in button_map.collisions(pos):
                        print(name)
                        match name.split("."):
                            case ["power", "on"]:
                                state.on = True
                                client.on()
                                redraw(screen, state)
                            case ["power", "off"]:
                                state.on = False
                                client.off()
                                redraw(screen, state)
                            case ["color", color]:
                                state.on = True
                                state.color = color
                                client.color(color)
                                redraw(screen, state)
                            case ["brightness", brightness]:
                                state.on = True
                                state.brightness = int(brightness)
                                client.brightness(int(brightness))
                                redraw(screen, state)

        clock.tick(30)

    client.off()
    pygame.quit()
