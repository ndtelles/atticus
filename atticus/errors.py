"""Define exceptions to be thown by atticus."""


class AtticusError(Exception):
    """Base class for Atticus exceptions."""


class AtticusAPIError(AtticusError):
    """Base class for Atticus API exceptions.

    Atticus API excpetions occur when an API call fails due
    to being invalid.
    """


class MockingbirdNotFound(AtticusAPIError):
    """Exception for when a mockingbird that is not loaded is referenced."""

    def __init__(self, mb_name: str) -> None:
        super().__init__("Mockingbird '{}' is not loaded".format(mb_name))


class MockingbirdAlreadyLoaded(AtticusAPIError):
    """Exception for when a mockingbird is loaded that already exists."""

    def __init__(self, mb_name: str) -> None:
        super().__init__("Mockingbird '{}' is already loaded".format(mb_name))


class MockingbirdNotRunning(AtticusAPIError):
    """Exception for when a command is invalid because the mockingbird is not running."""

    def __init__(self, mb_name: str) -> None:
        super().__init__("Mockingbird '{}' is not running".format(mb_name))


class MockingbirdRunning(AtticusAPIError):
    """Exception for when a command is invalid because the mockingbird is running."""

    def __init__(self, mb_name: str) -> None:
        super().__init__("Mockingbird '{}' is currently running".format(mb_name))


class ConfigError(AtticusError):
    """Base class for Config exceptions.

    These are exceptions that occur from the config reading, parsing, and
    validating process.
    """


class ConfigIOError(ConfigError):
    """Exception class for when unable to read from a config file."""


class InvalidConfig(ConfigError):
    """Exception class for when loading a config from a file fails."""


class BeakError(AtticusError):
    """Base class for beak interface errors."""

class BuffersContainerError(AtticusError):
    """Base class for buffers container errors."""

class BufferMissingError(BuffersContainerError):
    """Exception for when a process attemps to operate on a non-existant output buffer."""

class BufferAlreadyExists(BuffersContainerError):
    """Exception for when a buffer already exists"""
