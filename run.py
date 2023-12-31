import pygame

from govee_remote.client import GoveeClient
from govee_remote.gui import main

if __name__ == "__main__":
    client = GoveeClient(verbose=True)
    try:
        main(client)
    except KeyboardInterrupt:
        client.off()
        pygame.quit()
