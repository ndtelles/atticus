"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


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


class MockingbirdInvalidName(AtticusAPIError):
    """Exception for when a mockingbird is loaded with an invalid name."""

    def __init__(self, mb_name: str) -> None:
        super().__init__(
            "'{}' is not a valid Mockingbird name".format(mb_name))


class MockingbirdAlreadyLoaded(AtticusAPIError):
    """Exception for when a mockingbird is loaded that already exists."""

    def __init__(self, mb_name: str) -> None:
        super().__init__("Mockingbird '{}' is already loaded".format(mb_name))


class MockingbirdNotRunning(AtticusAPIError):
    """Command is invalid because the mockingbird is not running."""

    def __init__(self, mb_name: str) -> None:
        super().__init__("Mockingbird '{}' is not running".format(mb_name))


class MockingbirdRunning(AtticusAPIError):
    """Command is invalid because the mockingbird is running."""

    def __init__(self, mb_name: str) -> None:
        super().__init__(
            "Mockingbird '{}' is currently running".format(mb_name))


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


class MockingbirdError(AtticusError):
    """Base class for mockingbird errors"""


class MockingbirdUndefinedVar(MockingbirdError):
    """An undefined variable was encountered"""

    def __init__(self, var_name: str) -> None:
        super().__init__(
            "Undefined variable '{}' encountered.".format(var_name))


class MockingbirdUndefinedBeak(MockingbirdError):
    """An undefined beak was encountered"""

    def __init__(self, beak_name: str) -> None:
        super().__init__("Undefined beak '{}' encountered.".format(beak_name))
