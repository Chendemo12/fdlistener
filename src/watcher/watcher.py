# -*- coding:utf-8 -*-

"""
"""

from loguru import logger
from watchdog.events import (
    FileSystemEvent, FileMovedEvent, DirMovedEvent, FileOpenedEvent, FileClosedEvent,
    FileModifiedEvent, DirModifiedEvent, FileDeletedEvent, DirDeletedEvent, FileCreatedEvent, DirCreatedEvent,
    FileSystemEventHandler
)
from watchdog.observers import Observer

from .config import Container, convert_event_type


class Watcher(FileSystemEventHandler):
    """监听文件目录变动"""

    def __init__(self, conf: Container):
        self._running: bool = False
        self._config: Container = conf
        self.observer = Observer()

    @property
    def name(self) -> str:
        return self._config.path

    @property
    def config(self) -> Container:
        return self._config

    @property
    def running(self) -> bool:
        return self._running

    @property
    def event_handler(self):
        return self

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return (f"Watcher:{self.name!r}, kind:{self._config.kind}, on event:{[o.value for o in self._config.on]},"
                f" running:{self._running}")

    def start(self):
        self.observer.schedule(event_handler=self.event_handler,
                               path=self._config.path,
                               recursive=self._config.recursive, )
        self.observer.start()
        self._running = True

    def stop(self):
        self.observer.stop()
        self.observer.join()
        self._running = False

    def should_process(self, event: FileSystemEvent) -> bool:
        """

        :param event:
        :return:
        """
        should = self._config.make_reaction(convert_event_type(event.event_type, is_dir=event.is_directory))
        should and logger.info(event)

        return should

    def on_moved(self, event: DirMovedEvent | FileMovedEvent):
        """Called when a filereturn Config(containers=cont) or a directory is moved or renamed.

        :param event:
            Event representing file/directory movement.
        :type event:
            :class:`DirMovedEvent` or :class:`FileMovedEvent`
        """
        if not self.should_process(event):
            return

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent):
        """Called when a file or directory is created.

        :param event:
            Event representing file/directory creation.
        :type event:
            :class:`DirCreatedEvent` or :class:`FileCreatedEvent`
        """
        if not self.should_process(event):
            return

    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent):
        """Called when a file or directory is deleted.

        :param event:
            Event representing file/directory deletion.
        :type event:
            :class:`DirDeletedEvent` or :class:`FileDeletedEvent`
        """
        if not self.should_process(event):
            return

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        """Called when a file or directory is modified.

        :param event:
            Event representing file/directory modification.
        :type event:
            :class:`DirModifiedEvent` or :class:`FileModifiedEvent`
        """
        if not self.should_process(event):
            return

    def on_closed(self, event: FileClosedEvent):
        """Called when a file opened for writing is closed.

        :param event:
            Event representing file closing.
        :type event:
            :class:`FileClosedEvent`
        """
        if not self.should_process(event):
            return

    def on_opened(self, event: FileOpenedEvent):
        """Called when a file is opened.

        :param event:
            Event representing file opening.
        :type event:
            :class:`FileOpenedEvent`
        """
        if not self.should_process(event):
            return
