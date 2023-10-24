#!/bin/bash/env python3
# -*- coding: utf-8 -*-

"""
main
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from src.app import Application, LoguruHandler, AccessHandler

PROJECT_PATH: Path = Path(__file__).resolve().parent

os.path.exists(".env") and load_dotenv(".env")

DEBUG: bool = os.environ.get("DEBUG", False)
REMOTE_ADDRESS: str = os.environ.get("REMOTE_ADDRESS", "http://127.0.0.1:8080")


def logger_startup() -> None:
    logger.add(
        PROJECT_PATH / f"logs/{Path(__file__).parent.name}.log",
        level="DEBUG" if DEBUG else "WARNING",
        rotation="5 MB",
        retention="7 days",
        compression="tar.gz"
    )

    # 将默认的logging替换成loguru
    logging.captureWarnings(True)
    logging.root.handlers = [LoguruHandler()]

    for name in logging.root.manager.loggerDict.keys():
        logger_ = logging.getLogger(name)

        if name.startswith("http"):
            logger_.handlers = [AccessHandler()] if DEBUG else []  # 禁用HTTP日志，调试时可以打开

        elif name in ("asyncio", "concurrent"):
            logger_.handlers = [LoguruHandler()]
        elif name in ("websocket",):
            logger_.handlers = [AccessHandler()]

        else:
            logger_.handlers = []

        logger_.propagate = False


async def main():
    logger_startup()
    app = Application(remote_address=REMOTE_ADDRESS,
                      project_dir=PROJECT_PATH)

    await app.run()


if __name__ == '__main__':
    asyncio.run(main())
