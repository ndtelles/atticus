"""Beak provides abstract classes and methods for creating mockingbird communication interfaces."""

from abc import ABC, abstractmethod
from threading import Event
from typing import Dict

from .mockingbird import Mockingbird


class Beak(ABC):
    """Abstract class for creating communication interfaces that can be used by the mockingbird."""

    def __init__(self, stop_event: Event, config: Dict, mockingbird: Mockingbird) -> None:
        """The constructor for the Beak class."""

        self.config = config
        self.mockingbird = mockingbird
        self.stop_event = stop_event

    @abstractmethod
    def start(self) -> None:
        """Starts the communication interface."""
