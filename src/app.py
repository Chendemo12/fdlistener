# -*- coding: utf-8 -*-

import asyncio
import concurrent.futures
import inspect
import logging
from asyncio import Queue
from pathlib import Path
from typing import Optional, Callable, Any
from urllib.parse import urlparse, ParseResult

from loguru import logger

from src.pusher import HttpClient


class Application(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(
            self,
            remote_address: str,
            project_dir: Path = ""
    ):
        self._stop: bool = False
        self.executor: concurrent.futures.Executor = concurrent.futures.ThreadPoolExecutor()
        self.remote_address: ParseResult = urlparse(remote_address)
        self.project_dir: Path = project_dir
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
