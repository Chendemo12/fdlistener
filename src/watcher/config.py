# -*- coding:utf-8 -*-

"""
watchdog config
"""
import json
from enum import StrEnum
from typing import Literal, Optional

from pydantic import Field, BaseModel


class Event(StrEnum):
    """文件系统事件类型"""
    on_file_deleted: str = "fileDeleted"
    on_file_moved: str = "fileMoved"
    on_file_created: str = "fileCreated"
    on_file_modified: str = "fileModified"
    on_file_closed: str = "fileClosed"
    on_file_opened: str = "fileOpened"

    on_dir_deleted: str = "dirDeleted"
    on_dir_modified: str = "dirModified"
    on_dir_created: str = "dirCreated"
    on_dir_moved: str = "dirMoved"


class CallArgs(BaseModel):
    on: Event = Field(..., description="监听的文件系统事件类型")
    path: str = Field(..., description="目标名称")
    args: str = Field(...)


class Container(BaseModel):
    path: str = Field(..., min_length=1, description="目标路径")
    # 对于文件类型仅支持文件类型的事件;对于目录类型，不仅支持目录事件，同时还支持文件类型事件
    kind: Literal["dir", "file"] = Field("dir", description="目标类型")
    on: list[Event] = Field([Event.on_file_created], min_length=1, description="监听的文件系统事件类型")
    recursive: bool = Field(True, description="是否递归监控子目录")
    excluded_extensions: list[str] = Field([], description="排除的文件扩展名")
    # 此命令可以是一个系统调用，必须接受3个参数：CallArgs.on, CallArgs.path, CallArgs.args
    cmd: str = Field(..., description="当事件触发时执行的命令")

    @property
    def is_file_type(self) -> bool:
        return self.kind == "file"

    def make_reaction(self, event: Event | str) -> bool:
        """判断一个是否需要对一个事件做出反应，不区分事件大小写
        如果监听目标是一个文件：
            1. 忽略文件所属目录的全部事件

        如果目标是一个目录：
            1. 同时监听目录内文件的变动事件和目录的变动事件

        :param event 事件类型
        """
        if event is None:
            return False
        if self.is_file_type and str(event).upper() in (Event.on_dir_moved.upper(),
                                                        Event.on_dir_created.upper(), Event.on_dir_deleted.upper(),
                                                        Event.on_dir_modified.upper()):
            # 文件目标不对目录事件做出反应
            return False

        return str(event).upper() in (ev.value.upper() for ev in self.on)


class Config(BaseModel):
    """配置文件"""
    containers: list[Container] = Field([], description="监听目标")


class ConfigReader(object):

    @staticmethod
    def load_json_config(path: str) -> Config:
        with open(path, "r", encoding="utf-8") as f:
            cont = json.load(f)

        return Config(containers=cont)

    @staticmethod
    def load_toml_config(path: str) -> Config:
        with open(path, "r", encoding="utf-8") as f:
            cont = json.load(f)
        return Config(containers=cont)


def convert_event_type(name: Literal["moved", "deleted", "created", "modified", "closed", "opened"],
                       is_dir: bool) -> Optional[Event]:
    """转换事件类型"""
    match name:
        case "moved":
            return Event.on_dir_moved if is_dir else Event.on_file_moved
        case "deleted":
            return Event.on_dir_deleted if is_dir else Event.on_file_deleted
        case "created":
            return Event.on_dir_created if is_dir else Event.on_file_created
        case "modified":
            return Event.on_dir_modified if is_dir else Event.on_file_modified
        case "closed":
            return None if is_dir else Event.on_file_closed
        case "opened":
            return None if is_dir else Event.on_file_opened
        case _:
            return None
