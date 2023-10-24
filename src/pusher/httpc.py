# -*- coding: utf-8 -*-

"""
http client
"""
import dataclasses
import time
from functools import wraps
from typing import Union, Any, Optional
from urllib.parse import urljoin

import httpx


@dataclasses.dataclass(frozen=True)
class Interface(object):
    """通用返回值"""
    result: bool
    data: Any
    error: Optional[Union[Exception, httpx.Response]]
    elapsed_time: float

    def __bool__(self) -> bool:
        return bool(self.result)

    def __str__(self) -> str:
        s = f"{self.__class__.__name__}(result={self.result}, data={self.data}, "

        if isinstance(self.error, httpx.Response):
            s += f"error={self.error.json()})"
        else:
            s += f"error={self.error})"

        return s


def response_adaptor(func):
    """返回值封装"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Interface:
        s: float = time.time()
        try:
            response: httpx.Response = await func(*args, **kwargs)

            if response.status_code == 200:
                return Interface(result=True,
                                 data=response.json(),
                                 error=None,
                                 elapsed_time=time.time() - s)

            return Interface(result=False,
                             data=response,
                             error=response,
                             elapsed_time=time.time() - s)

        except (httpx.ConnectTimeout, httpx.ConnectError, Exception) as e:
            return Interface(result=False, data=None, error=e, elapsed_time=time.time() - s)

    return wrapper


class HttpClient(object):
    """客户端基类"""

    timeout: int = 10

    def __init__(self, addr: str, tsl: bool = False):
        self.addr: str = f"https://{addr}" if tsl else f"http://{addr}"
        self.header: dict = {"Connection": "keep-alive"}
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=10)

    @response_adaptor
    async def get(self, path: str, *, headers: dict = None, **kwargs):
        return await self._client.get(
            urljoin(self.addr, path),
            params=kwargs.get("params", None),
            timeout=kwargs.get("timeout", self.__class__.timeout),
            headers=self.header | headers if headers else self.header
        )

    @response_adaptor
    async def post(self, path: str, *, headers: dict = None, **kwargs):
        return await self._client.post(
            urljoin(self.addr, path),
            json=kwargs.get("json_data", None),
            data=kwargs.get("data", None),
            params=kwargs.get("params", None),
            timeout=kwargs.get("timeout", self.__class__.timeout),
            files=kwargs.get("form_data", None),
            headers=self.header | headers if headers else self.header,
        )

    @response_adaptor
    async def put(self, path: str, *, headers: dict = None, **kwargs):
        return await self._client.put(
            urljoin(self.addr, path),
            json=kwargs.get("json_data", None),
            timeout=kwargs.get("timeout", self.__class__.timeout),
            headers=headers,
        )

    @response_adaptor
    async def patch(self, path: str, *, headers: dict = None, **kwargs):
        return await self._client.patch(
            urljoin(self.addr, path),
            json=kwargs.get("json_data", None),
            timeout=kwargs.get("timeout", self.__class__.timeout),
            params=kwargs.get("params", None),
            headers=self.header | headers if headers else self.header,
        )

    @response_adaptor
    async def delete(self, path: str, *, headers: dict = None, **kwargs):
        return await self._client.delete(
            urljoin(self.addr, path),
            params=kwargs.get("params", None),
            timeout=kwargs.get("timeout", self.__class__.timeout),
            headers=self.header | headers if headers else self.header,
        )
