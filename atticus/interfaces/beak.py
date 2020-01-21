"""Provides abstract class for creating mockingbird comm interfaces."""

import logging
from abc import abstractmethod
from contextlib import AbstractContextManager
from threading import Event, Thread
from types import TracebackType
from typing import Any, Callable, Tuple, Type
from typing import Optional as Opt  # Shorten name

from ..config import Config


class Beak(AbstractContextManager):
    """Abstract class for creating interfaces used by the mockingbird."""

    def __init__(self, config: Config.Interface,
                 request: Callable[[Any, str], None],
                 receive: Callable[[bool, Opt[float]], Opt[Tuple[Any, str]]],
                 register_request: Callable[[str, Opt[str]], None],
                 register_default_request: Callable[[str], None]) -> None:
        """The constructor for the Beak class."""

        self.__request_func = request
        self.__receive_func = receive
        self.__register_request_func = register_request
        self.__register_default_request_func = register_default_request
        self.__booted = Event()  # Indicates that startup process finished
        self.__io_thread = Thread(target=self.__io_loop)

        self._stop_event = Event()
        self._config = config
        self._log = logging.getLogger(config.name)

    def __enter__(self) -> 'Beak':
        self.start()
        return self

    def __exit__(self, ex: Opt[Type[BaseException]], val: Opt[BaseException],
                 trb: Opt[TracebackType]) -> None:
        self.stop()

    @property
    def config(self) -> Config.Interface:
        """Return the configuration of the interface"""

        return self._config

    @property
    def name(self) -> str:
        """Return interface name"""

        return self._config.name

    @property
    def log(self) -> logging.Logger:
        return self._log

    def start(self) -> None:
        """Starts the communication interface."""

        self._stop_event.clear()
        self.__io_thread = Thread(target=self.__io_loop)
        self.__io_thread.start()

        # Block until the interface finishes starting up.
        # This is meant to guarantee that after start returns, the caller
        # has a useable interface. For example, with TCPServer, this guarantees
        # the server socket has been opened and can accept clients before start
        # returns.
        self.__booted.wait()

    def stop(self) -> None:
        """Stops the communication interface."""
        self._stop_event.set()
        self.__io_thread.join(5)

        if self.__io_thread.is_alive():
            self._log.error(
                "Failed to join interface thread. Interface thread orphaned.")

    def __io_loop(self) -> None:
        """The main loop run by the IO thread."""

        # Boot the interface
        self._boot_beak()
        self.__booted.set()

        # Let the interface run
        self._run_beak()
        self._stop_event.wait()

        self.__booted.clear()
        self._shutdown_beak()

    def _mb_request(self, key: Any, msg: str) -> None:
        # TODO: Allow request to be dropped if queue is full
        self.__request_func(key, msg)

    def _mb_receive(self, block: bool = True, timeout: Opt[float] = None
                    ) -> Opt[Tuple[Any, str]]:
        return self.__receive_func(block, timeout)

    def _mb_register_request(self, req: str, resp: Opt[str] = None) -> None:
        self.__register_request_func(req, resp)

    def _mb_register_default_request(self, resp: str) -> None:
        self.__register_default_request_func(resp)

    @abstractmethod
    def _boot_beak(self) -> None:
        """Method that is called before starting the io loop.

        Useful for initializing any file descriptors used by the interface
        and opening connections
        """

    @abstractmethod
    def _run_beak(self) -> None:
        """Method that is the main body of the io loop.

        This is where your IO interface should do most of its work such
        as reading and writing from buffers. It is the responsibility of
        the contents of _run to use the CPU efficiently. Avoid busy-waiting.
        The method can either create its own threads to do its job and let
        _run return immediately after starting the threads, or use a loop
        inside the run method that exits when stop_event is set.
        """

    @abstractmethod
    def _shutdown_beak(self) -> None:
        """Method that is called after the stop event is received.

        This is useful for closing any file descriptors used by the interface.
        """
