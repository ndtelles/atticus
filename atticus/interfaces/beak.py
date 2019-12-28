"""Beak provides abstract classes and methods for creating mockingbird communication interfaces."""

from abc import ABC, abstractmethod
from collections import deque
from threading import Event, Lock, Thread
from typing import Any, Callable, Deque, Dict, Optional, Tuple

from ._helpers.buffers_container import BuffersContainer


class Beak(ABC):
    """Abstract class for creating communication interfaces that can be used by the mockingbird."""

    # All interfaces share input buffer so that the input (and thus output) is
    # handeled as close to FIFO as possible
    __input_buffer: Deque[Tuple[str, Callable[[str], None]]] = deque(
        maxlen=512)
    __input_buffer_lock = Lock()
    input_ready = Event()

    @staticmethod
    def read_buffer() -> Tuple[Optional[str], Optional[Callable[[str], None]]]:
        """Read from the input buffer shared by all beak interfaces.

        Pops from the buffer a tuple reprsenting the oldest message (FIFO) in the
        input buffer as well as a callable function for responding to the input.
        If the message popped from the input buffer was the last message in the
        buffer then the input_ready event is set back to false.
        """
        with Beak.__input_buffer_lock:
            data = Beak.__input_buffer.popleft() if Beak.__input_buffer else (None, None)

            if not Beak.__input_buffer:
                Beak.input_ready.clear()

            return data

    def __init__(self, config: Dict) -> None:
        """The constructor for the Beak class."""

        self.__io_thread = Thread(target=self.__io_loop)
        self.__stop = False

        # Vars safe to use from inheriting interfaces
        self._config = config
        self._output_buffers = BuffersContainer()

    def __del__(self) -> None:
        """The desctructor for the Beak class.

        Stop the io thread if it is still running.
        """

        if self.__io_thread.is_alive():
            self.stop()

    def start(self) -> None:
        """Starts the communication interface."""

        self.__stop = False
        self.__io_thread.start()

    def stop(self) -> None:
        """Stops the communication interface."""

        self.__stop = True
        self.__io_thread.join()

    def __io_loop(self) -> None:
        """The main loop run by the IO thread."""

        self._start()

        while not self.__stop:
            self._run()

        self._stop()

    def _receive(self, msg: str, output_buffer_key: Any) -> None:
        """Called by IO interfaces to stash received input into the input buffer.

        A function for responding to the input is also stashed with the input.
        This function allows whoever reads the input to also respond to the input
        by writing to the correct output buffer.
        The input_ready event is also set so watchers know their is input available.
        """

        # Provide callback for mockingbird to respond to input
        def respond(response: str) -> None:
            self._output_buffers.append(output_buffer_key, response)

        with Beak.__input_buffer_lock:
            Beak.__input_buffer.append((msg, respond))
            Beak.input_ready.set()

    @abstractmethod
    def _start(self) -> None:
        """Method that is called before starting the io loop.

        This is useful for initializing any file descriptors used by the interface.
        """

    @abstractmethod
    def _stop(self) -> None:
        """Method that is called after the io loop is stopped.

        This is useful for closing any file descriptors used by the interface.
        """

    @abstractmethod
    def _run(self) -> None:
        """Method that is the main body of the io loop.

        This is where your IO interface should do most of its work such
        as reading and writing from buffers. Since the io loop is a simple
        while loop, it is the responsibility of the contents of _run to use
        the CPU efficiently. The contents of the method should not block any
        longer than a second (use timeouts!) and should use events or polling
        instead of busy waiting.
        """
