from collections.abc import Iterator
from dataclasses import dataclass
from itertools import batched

import pygame
from matplotlib.colors import CSS4_COLORS
from matplotlib.colors import rgb_to_hsv
from matplotlib.colors import to_rgb

from govee_remote.client import GoveeClient
from govee_remote.color import get_color
from govee_remote.color import get_luma


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


def redraw(screen: pygame.Surface, state: State) -> ButtonMap:
    button_map = ButtonMap()

    screen.fill("white")

    names = sorted(CSS4_COLORS, key=lambda c: tuple(rgb_to_hsv(to_rgb(c))))

    font = pygame.font.SysFont("Arial", 14)
    font_large = pygame.font.SysFont("Arial", 22, bold=1)

    button_width = 60
    button_height = 30
    large_button_width = 90
    large_button_height = 45
    cell_width = 190
    cell_height = 40
    left_padding = 20
    top_padding = 100

    on_color = "yellow" if state.on else "lightgray"
    on_rect = pygame.Rect(left_padding, 30, large_button_width, large_button_height)
    button_map.register("power.on", on_rect)
    pygame.draw.rect(screen, get_color(on_color), on_rect)
    pygame.draw.rect(screen, "black", on_rect, width=2)
    on_text = font_large.render("On", True, "black")
    screen.blit(on_text, on_text.get_rect(center=on_rect.center))

    off_color = "lightgray" if state.on else "yellow"
    off_rect = pygame.Rect(
        left_padding + large_button_width + 20,
        30,
        large_button_width,
        large_button_height,
    )
    button_map.register("power.off", off_rect)
    pygame.draw.rect(screen, get_color(off_color), off_rect)
    pygame.draw.rect(screen, "black", off_rect, width=2)
    off_text = font_large.render("Off", True, "black")
    screen.blit(off_text, off_text.get_rect(center=off_rect.center))

    for col, batch in enumerate(batched(names, 20)):
        for row, name in enumerate(batch):
            rect = pygame.Rect(
                left_padding + col * cell_width,
                top_padding + row * cell_height,
                button_width,
                button_height,
            )
            pygame.draw.rect(screen, get_color(name), rect)
            pygame.draw.rect(screen, "black", rect, width=2)
            color_name = font.render(name.capitalize(), 1, "black")
            screen.blit(
                color_name,
                color_name.get_rect(left=rect.right + 10, centery=rect.centery),
            )
            button_map.register(
                f"color.{name}",
                pygame.Rect(
                    left_padding + col * cell_width,
                    top_padding + row * cell_height,
                    cell_width - 10,
                    button_height,
                ),
            )
            if name == state.color:
                color = "black" if get_luma(get_color(name)) > 130 else "white"
                checkmark = font_large.render("X", 1, color)
                screen.blit(checkmark, checkmark.get_rect(center=rect.center))

    row += 1

    brightness_label = font_large.render("Brightness", 1, "black")
    screen.blit(
        brightness_label,
        (left_padding + col * cell_width, top_padding + row * cell_height + 5),
    )

    brightnesses = [1, *range(10, 101, 10)]
    brightnesses.reverse()
    for row, brightness in enumerate(brightnesses, start=row + 1):
        rect = pygame.Rect(
            left_padding + col * cell_width,
            top_padding + row * cell_height,
            button_width,
            button_height,
        )
        pygame.draw.rect(
            screen, tuple(int(255 * brightness / 100) for _ in range(3)), rect
        )
        pygame.draw.rect(screen, "black", rect, width=2)
        brightness_name = font.render(f"{brightness}%", 1, "black")
        screen.blit(
            brightness_name,
            brightness_name.get_rect(left=rect.right + 10, centery=rect.centery),
        )
        button_map.register(
            f"brightness.{brightness}",
            pygame.Rect(
                left_padding + col * cell_width,
                top_padding + row * cell_height,
                cell_width - 10,
                button_height,
            ),
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

    hits = set()

    while running:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    hits = set(button_map.collisions(pos))
                case pygame.MOUSEBUTTONUP:
                    pos = event.pos
                    for name in button_map.collisions(pos):
                        if name in hits:
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
