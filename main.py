#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
main
"""

import asyncio
import os
import sys
from pathlib import Path

if os.path.exists(_path := Path(__file__).resolve().parent / "site-packages"):
    sys.path.append(str(_path))

CONFIG_PATH: str = "/etc/opt/apps/fdlistener"

if __name__ == '__main__':
    from dotenv import load_dotenv
    from src.app import Application, logger_startup

    os.path.exists(CONFIG_PATH + "/.env") and load_dotenv(CONFIG_PATH + "/.env")


    async def main():
        logger_startup()
        app = Application(
            remote_address=os.environ.get("REMOTE_ADDRESS", "http://127.0.0.1:8080")
        )

        await app.run(config_filepath=os.environ.get("CONFIG_FILEPATH", CONFIG_PATH + "/config.json"))


    asyncio.run(main())
