"""Provides a thread-safe container of buffers that can be selected by key"""

from collections import deque
from threading import RLock
from typing import Any, Deque, Dict, List, Optional, Set

from ...errors import BufferAlreadyExists, BufferMissingError


class BuffersContainer:
    """Provides a thread-safe container of buffers that can be selected by key"""

    def __init__(self) -> None:
        self._buffers = {} # type: Dict[Any, Deque[str]]
        self._lock = RLock()

        # Used to notify callers of buffers that have brand new data.
        # Buffers are removed from the set when either a caller
        # acknowledges there is new data or the buffer becomes empty
        self._new_data: Set[Any] = set()

    def create(self, buffer_key: Any) -> None:
        """Create a new buffer and store it in the buffer container.

        Throws BufferAlreadyExists if a buffer with that key already exists.
        """

        with self._lock:
            if buffer_key in self._buffers:
                raise BufferAlreadyExists

            self._buffers[buffer_key] = deque(maxlen=512)

    def append(self, buffer_key: Any, msg: str) -> None:
        """Append a message to a buffer.

        Adding new data to a buffer adds the buffer to the new_data set which
        allows a caller to see that there is brand new data for that buffer.
        """

        with self._lock:
            if buffer_key not in self._buffers:
                raise BufferMissingError

            self._buffers[buffer_key].append(msg)
            self._new_data.add(buffer_key)

    def pop(self, buffer_key: Any) -> Optional[str]:
        """Pops off a message from a buffer in FIFO order

        If buffer does not exist, pop throws BufferMissingError.
        If there is nothing in the buffer, return None
        """

        with self._lock:
            if buffer_key not in self._buffers:
                raise BufferMissingError

            if not self._buffers[buffer_key]:
                return None

            val = self._buffers[buffer_key].popleft()

            if self.is_empty(buffer_key):
                self._new_data.discard(buffer_key)

            return val

    def delete(self, buffer_key: Any) -> None:
        """Delete a buffer.

        This in turn also deletes the new data notification for the buffer
        if it exists.
        Throws BufferMissingError if a buffer with that key does not exist.
        """

        with self._lock:
            if buffer_key not in self._buffers:
                raise BufferMissingError

            del self._buffers[buffer_key]
            self._new_data.discard(buffer_key)

    def new_data(self, ack: bool = True) -> List[Any]:
        """Returns a list of buffer keys belonging to buffers that have new data
        unacknowledged by the user.

        If ack is true, calling the function removes all new_data notifications from
        the new_data set.
        """
        with self._lock:
            val = list(self._new_data)

            if ack:
                self._new_data.clear()

            return val

    def has_new_data(self, buffer_key: Any, ack: bool = True) -> bool:
        """Returns whether a buffer has new unacknowladed data.

        If ack is true, calling the function removes the notification for
        the specified buffer from the new_data set. Not having "new" data
        should not be confused with not having data in the buffer.
        """
        with self._lock:
            val = buffer_key in self._new_data

            if ack:
                self._new_data.discard(buffer_key)

            return val

    def is_empty(self, buffer_key: Any) -> bool:
        """Indicates whether a buffer has any data in it."""

        with self._lock:
            if buffer_key not in self._buffers:
                raise BufferMissingError

            return len(self._buffers[buffer_key]) == 0
