from __future__ import annotations

import os.path
from collections.abc import Iterator
from dataclasses import asdict
from dataclasses import dataclass
from itertools import batched

import pygame
import yaml
from matplotlib.colors import CSS4_COLORS
from matplotlib.colors import rgb_to_hsv
from matplotlib.colors import to_rgb

from govee_remote.client import GoveeClient
from govee_remote.color import get_color
from govee_remote.color import get_luma
from govee_remote.color import KELVIN_RGB
from govee_remote.color import RGB

STATE_FILE = "data/state.yaml"


@dataclass
class State:
    color: str = "kelvin"
    brightness: int = 100
    on: bool = True
    kelvin: int = 3000

    def save(self) -> None:
        with open(STATE_FILE, "w") as fp:
            yaml.safe_dump({"state": asdict(self)}, fp)

    @classmethod
    def load(cls) -> State:
        if not os.path.exists(STATE_FILE):
            return cls()
        with open(STATE_FILE) as fp:
            return State(**yaml.safe_load(fp)["state"])


class ButtonMap:
    def __init__(self) -> None:
        self._map: dict[str, pygame.Rect] = {}

    def register(self, key: str, rect: pygame.Rect) -> None:
        self._map[key] = rect

    def collisions(self, pos: tuple[int, int]) -> Iterator[str]:
        for key, rect in self._map.items():
            if rect.collidepoint(pos):
                yield key


class UIConfig:
    def __init__(self) -> None:
        self.button_width = 60
        self.button_height = 30
        self.large_button_width = 90
        self.large_button_height = 45
        self.cell_width = 190
        self.cell_height = 40
        self.left_padding = 20
        self.top_padding = 100
        self.font = pygame.font.SysFont("Arial", 14)
        self.font_large = pygame.font.SysFont("Arial", 22, bold=1)


def add_button(
    conf: UIConfig,
    button_map: ButtonMap,
    color: RGB | str,
    row: int,
    col: int,
    label: str,
    name: str,
    screen: pygame.Surface,
) -> pygame.Rect:
    rect = pygame.Rect(
        conf.left_padding + col * conf.cell_width,
        conf.top_padding + row * conf.cell_height,
        conf.button_width,
        conf.button_height,
    )
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, "black", rect, width=2)
    color_name = conf.font.render(label, 1, "black")
    screen.blit(
        color_name,
        color_name.get_rect(left=rect.right + 10, centery=rect.centery),
    )
    button_map.register(
        name,
        pygame.Rect(
            conf.left_padding + col * conf.cell_width,
            conf.top_padding + row * conf.cell_height,
            conf.cell_width - 10,
            conf.button_height,
        ),
    )
    return rect


def add_checkmark(
    conf: UIConfig, screen: pygame.Surface, rect: pygame.Rect, color: RGB | str
) -> None:
    checkmark = conf.font_large.render("X", 1, color)
    screen.blit(checkmark, checkmark.get_rect(center=rect.center))


def redraw(screen: pygame.Surface, state: State) -> ButtonMap:
    button_map = ButtonMap()

    screen.fill("white")

    names = sorted(
        filter(lambda c: "grey" not in c, CSS4_COLORS),
        key=lambda c: tuple(rgb_to_hsv(to_rgb(c))),
    )

    conf = UIConfig()

    on_color = "yellow" if state.on else "lightgray"
    on_rect = pygame.Rect(
        conf.left_padding, 30, conf.large_button_width, conf.large_button_height
    )
    button_map.register("power.on", on_rect)
    pygame.draw.rect(screen, get_color(on_color), on_rect)
    pygame.draw.rect(screen, "black", on_rect, width=2)
    on_text = conf.font_large.render("On", True, "black")
    screen.blit(on_text, on_text.get_rect(center=on_rect.center))

    off_color = "lightgray" if state.on else "yellow"
    off_rect = pygame.Rect(
        conf.left_padding + conf.large_button_width + 20,
        30,
        conf.large_button_width,
        conf.large_button_height,
    )
    button_map.register("power.off", off_rect)
    pygame.draw.rect(screen, get_color(off_color), off_rect)
    pygame.draw.rect(screen, "black", off_rect, width=2)
    off_text = conf.font_large.render("Off", True, "black")
    screen.blit(off_text, off_text.get_rect(center=off_rect.center))

    for col, batch in enumerate(batched(names, 20)):
        for row, name in enumerate(batch):
            color = get_color(name)
            rect = add_button(
                conf=conf,
                button_map=button_map,
                color=color,
                row=row,
                col=col,
                label=name.capitalize(),
                name=f"color.{name}",
                screen=screen,
            )
            if name == state.color:
                add_checkmark(
                    conf=conf,
                    screen=screen,
                    rect=rect,
                    color="black" if get_luma(color) > 130 else "white",
                )

    row += 1

    brightness_label = conf.font_large.render("Brightness", 1, "black")
    screen.blit(
        brightness_label,
        (
            conf.left_padding + col * conf.cell_width,
            conf.top_padding + row * conf.cell_height + 5,
        ),
    )

    brightnesses = [1, *range(10, 101, 10)]
    brightnesses.reverse()
    for row, brightness in enumerate(brightnesses, start=row + 1):
        c = int(255 * brightness / 100)
        rect = add_button(
            conf=conf,
            button_map=button_map,
            color=(c, c, c),
            row=row,
            col=col,
            label=f"{brightness}%",
            name=f"brightness.{brightness}",
            screen=screen,
        )
        if brightness == state.brightness:
            add_checkmark(
                conf=conf,
                screen=screen,
                rect=rect,
                color="black" if brightness >= 50 else "white",
            )

    row += 1

    kelvin_label = conf.font_large.render("Illumination Mode", 1, "black")
    screen.blit(
        kelvin_label,
        (
            conf.left_padding + col * conf.cell_width,
            conf.top_padding + row * conf.cell_height + 5,
        ),
    )

    row += 1

    rect = add_button(
        conf=conf,
        button_map=button_map,
        color=KELVIN_RGB[state.kelvin],
        row=row,
        col=col,
        label=f"{state.kelvin}K",
        name="color.kelvin",
        screen=screen,
    )
    if state.color == "kelvin":
        add_checkmark(conf=conf, screen=screen, rect=rect, color="black")

    kelvin_plus = pygame.Rect(
        rect.right + 100,
        conf.top_padding + row * conf.cell_height,
        conf.button_height,
        conf.button_height,
    )
    pygame.draw.rect(screen, "lightblue", kelvin_plus)
    pygame.draw.rect(screen, "black", kelvin_plus, width=2)
    plus_text = conf.font.render("+", 1, "black")
    screen.blit(
        plus_text,
        plus_text.get_rect(center=kelvin_plus.center),
    )
    button_map.register("kelvin.plus", kelvin_plus)

    kelvin_minus = pygame.Rect(
        kelvin_plus.right + 10,
        conf.top_padding + row * conf.cell_height,
        conf.button_height,
        conf.button_height,
    )
    pygame.draw.rect(screen, "red", kelvin_minus)
    pygame.draw.rect(screen, "black", kelvin_minus, width=2)
    minus_text = conf.font.render("-", 1, "black")
    screen.blit(
        minus_text,
        minus_text.get_rect(center=kelvin_minus.center),
    )
    button_map.register("kelvin.minus", kelvin_minus)

    pygame.display.flip()

    return button_map


def handle_click(
    name: str, state: State, client: GoveeClient, screen: pygame.Surface
) -> None:
    match name.split("."):
        case ["power", "on"]:
            state.on = True
            client.on()
            redraw(screen, state)
        case ["power", "off"]:
            state.on = False
            client.off()
            redraw(screen, state)
        case ["color", "kelvin"]:
            state.on = True
            state.color = "kelvin"
            client.color_kelvin(state.kelvin)
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
        case ["kelvin", "plus"]:
            state.kelvin = min(state.kelvin + 100, 9000)
            if state.color == "kelvin":
                client.color_kelvin(state.kelvin)
            redraw(screen, state)
        case ["kelvin", "minus"]:
            state.kelvin = max(state.kelvin - 100, 2000)
            if state.color == "kelvin":
                client.color_kelvin(state.kelvin)
            redraw(screen, state)


def loop(
    state: State, client: GoveeClient, screen: pygame.Surface, button_map: ButtonMap
) -> None:
    hits = set()
    clock = pygame.time.Clock()
    running = True
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
                            handle_click(
                                name=name, state=state, client=client, screen=screen
                            )
        clock.tick(30)


def main(client: GoveeClient) -> None:
    pygame.init()
    pygame.display.set_caption("Govee Remote")
    client.on()
    state = State.load()
    if state.color == "kelvin":
        client.color_kelvin(state.kelvin)
    else:
        client.color(state.color)
    client.brightness(state.brightness)
    screen = pygame.display.set_mode((1600, 900))
    button_map = redraw(screen, state)
    loop(state=state, client=client, screen=screen, button_map=button_map)
    state.save()
    client.off()
    pygame.quit()
