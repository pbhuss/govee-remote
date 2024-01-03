from __future__ import annotations

import json
import socket
import time
from enum import StrEnum
from typing import Any

from govee_remote.color import get_color
from govee_remote.color import RGB

DEVICE_IP = "192.168.50.82"
DEFAULT_PORT = 4003


class GoveeClient:
    def __init__(
        self,
        device_ip: str = DEVICE_IP,
        port: int = DEFAULT_PORT,
        verbose: bool = False,
    ) -> None:
        self._udp_ip = device_ip
        self._udp_port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._verbose = verbose

    def on(self) -> None:
        data = {"value": 1}
        self._send_command(Command.ON_OFF, data)

    def off(self) -> None:
        data = {"value": 0}
        self._send_command(Command.ON_OFF, data)

    def color(self, name: str) -> None:
        self.color_rgb(get_color(name))

    def color_rgb(self, rgb: RGB) -> None:
        if not all(0 <= x <= 255 for x in rgb):
            raise ValueError(f"Invalid color: {rgb}")
        data = {
            "color": dict(zip("rgb", rgb)),
            "colorTemInKelvin": 0,
        }
        self._send_command(Command.COLOR, data)

    def color_kelvin(self, kelvin: int) -> None:
        if not 2000 <= kelvin <= 9000:
            raise ValueError(f"Invalid kelvin: {kelvin}")
        data = {
            "color": {"r": 0, "g": 0, "b": 0},
            "colorTemInKelvin": kelvin,
        }
        self._send_command(Command.COLOR, data)

    def brightness(self, brightness: int) -> None:
        if not 1 <= brightness <= 100:
            raise ValueError(f"Invalid brightness: {brightness}")
        data = {"value": brightness}
        self._send_command(Command.BRIGHTNESS, data)

    def _send_command(self, command: Command, data: dict[str, Any]) -> None:
        message = {
            "msg": {
                "cmd": str(command),
                "data": data,
            }
        }
        json_result = json.dumps(message).encode("utf-8")
        if self._verbose:
            print(f"Sending: {message} to {self._udp_ip}")
        self._sock.sendto(json_result, (self._udp_ip, self._udp_port))
        time.sleep(0.05)


class Command(StrEnum):
    ON_OFF = "turn"
    COLOR = "colorwc"
    BRIGHTNESS = "brightness"
