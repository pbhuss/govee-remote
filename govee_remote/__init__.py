import pygame

from govee_remote.client import GoveeClient
from govee_remote.gui import main


def start() -> None:
    with open("data/ip.txt") as fp:
        device_ip = fp.read().strip()
    client = GoveeClient(device_ip, verbose=True)
    try:
        main(client)
    except KeyboardInterrupt:
        client.off()
        pygame.quit()
