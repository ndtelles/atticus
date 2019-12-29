"""Parses and validates mockingbird configuration files."""

from typing import Any, Dict

import schema as sch
import yaml

from .errors import ConfigIOError, InvalidConfig

IP_REG = sch.Regex(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
SCHEMA = sch.Schema({
    'name': sch.And(str, sch.Regex(r'^[\w\d]+$')),
    'interface': sch.Or(
        {
            # TODO: Interfaces should have names
            'tcp': {
                'address': IP_REG,
                'port': int
            },
        },
        # Future interfaces here
    ),
    sch.Optional('properties'): {
        sch.Optional('case_sensitive'): bool,
        sch.Optional('terminator'): sch.And(
            str, sch.Use(str.lower), lambda s: s in ('crlf', 'lf', 'none'))
    },
    # TODO: Should requests belong to a specific interface?
    'requests': {str: str}
})


def parse_file(file_path: str) -> Dict[str, Any]:
    """Open the yaml file at the provided path and parse it to generate a config object."""

    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            return SCHEMA.validate(config)

    except EnvironmentError as ex:
        raise ConfigIOError(
            "Unable to read file '{}'. {}".format(file_path, ex)) from ex
    except yaml.YAMLError as ex:
        raise InvalidConfig("Invalid configuration:\n{}".format(ex)) from ex
