# Govee Remote

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pbhuss/govee-remote/main.svg)](https://results.pre-commit.ci/latest/github/pbhuss/govee-remote/main)

Controls Govee smart lights via the LAN API on supported devices.

LAN Control must be enabled for your device in the Govee app. See https://app-h5.govee.com/user-manual/wlan-guide

## Installation
1. Install Python 3.12 (https://www.python.org/downloads/)
2. Install Poetry (https://python-poetry.org/docs/#installation)
3. Open `data/ip.txt` and update the IP to the local IP of your Govee device (autodetection coing soon)
4. Run `poetry install` from the project directory

## Running
Run `poetry run remote`
