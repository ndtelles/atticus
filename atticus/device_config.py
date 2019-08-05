"""Parses and validates mockingbird configuration files."""

import typing

import yaml
from schema import And, Optional, Or, Regex, Schema, Use

from .errors import ConfigIOError, InvalidConfig

IP_REG = Regex(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
SCHEMA = Schema({
    'name': And(str, Regex(r'^[\w\d]+$')),
    'interface': Or(
        {
            'tcp': {
                'address': IP_REG,
                'port': int
            },
        },
        # Future interfaces here
    ),
    Optional('properties'): {
        Optional('case_sensitive'): bool,
        Optional('terminator'): And(str, Use(str.lower), lambda s: s in ('crlf', 'lf', 'none'))
    },
    'requests': {str: str}
})


def parse_file(file_path: str) -> typing.Dict:
    """Open the yaml file at the provided path and parse it to generate a config object."""

    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            return config if SCHEMA.is_valid(config) else None
    except EnvironmentError as ex:
        raise ConfigIOError(
            "Unable to read file '{}'. {}".format(file_path, ex)) from ex
    except yaml.YAMLError as ex:
        raise InvalidConfig("Invalid configuration:\n{}".format(ex)) from ex
