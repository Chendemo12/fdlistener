# -*- coding: utf-8 -*-

import asyncio
import concurrent.futures
import inspect
import logging
import os
from asyncio import Queue
from pathlib import Path
from typing import Optional, Callable, Any
from urllib.parse import urlparse, ParseResult

from loguru import logger
from src.pusher import HttpClient

PROJECT_PATH: Path = Path(__file__).resolve().parent.parent


class Application(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, remote_address: str):
        self._stop: bool = False
        self.executor: concurrent.futures.Executor = concurrent.futures.ThreadPoolExecutor()
        self.remote_address: ParseResult = urlparse(remote_address)
        self.project_dir: Path = PROJECT_PATH
        self.sub_queue: Optional[Queue] = None

        self.pusher: HttpClient = HttpClient(
            self.remote_address.netloc,
            tsl=self.remote_address.scheme == "https"
        )

    def stop(self):
        self._stop = True

    async def run(self):
        self._stop = False
        self.sub_queue = Queue()

        logger.info("application started!")

    async def run_sync_func(self, func: Callable, timeout: int = 0, on_timeout: Callable = None) -> Any:
        """
        异步的执行同步任务

        :param func: 同步函数
        :param timeout: 超时事件
        :param on_timeout: 若超时时间有效且此回调不为None,则在超时时触发此回调，否则将 raise asyncio.TimeoutError
        """
        target = asyncio.get_event_loop().run_in_executor(self.executor, func)
        if timeout is None or timeout <= 0:
            return await target

        try:
            result = await asyncio.wait_for(target, timeout)
            return result
        except asyncio.TimeoutError as e:
            if on_timeout is not None:
                if inspect.iscoroutinefunction(on_timeout):
                    await on_timeout()
                else:
                    on_timeout()
            else:
                raise e

    def block_execute_func(self, func: Callable, timeout: int = 0) -> Any:
        """阻塞的允许一个同步函数，此操作会阻塞事件循环"""
        future = self.executor.submit(func)
        try:
            result = future.result(timeout=timeout)
            return result

        except concurrent.futures.TimeoutError:
            logger.warning(f"{func.__name__} execute timeout")
            future.cancel()  # 如果超时，取消 Future 对象

    def __del__(self):
        self.executor.shutdown()


class LoguruHandler(logging.Handler):
    _logger = logger

    def emit(self, record):
        try:
            level = self._logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        self._logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class AccessHandler(LoguruHandler):
    _logger = logger.bind(name="access")


def logger_startup() -> None:
    _debug: bool = os.environ.get("DEBUG", False)
    logger.add(
        os.path.join(os.environ.get("FDLISTENER_LOG_DIR", PROJECT_PATH), f"logs/{PROJECT_PATH.name}.log"),
        level="DEBUG" if _debug else "WARNING",
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
            logger_.handlers = [AccessHandler()] if _debug else []  # 禁用HTTP日志，调试时可以打开

        elif name in ("asyncio", "concurrent"):
            logger_.handlers = [LoguruHandler()]
        elif name in ("websocket",):
            logger_.handlers = [AccessHandler()]

        else:
            logger_.handlers = []

        logger_.propagate = False
