"""Parses and validates mockingbird configuration files."""

from typing import Any, Dict, ValuesView

import schema as sch
import yaml

from .errors import ConfigIOError, InvalidConfig

SAFE_STR_REG = sch.Regex(r'^[\w\d]+$')

# Regex for validating ip addressses
IP_REG = sch.Regex(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

TCP_SCHEMA = sch.Schema({
    'type': 'tcp_server',
    'address': IP_REG,
    'port': sch.And(sch.Use(int), lambda n: 0 <= n <= 65535),
    sch.Optional('line_ending', default="\n"): str,
    sch.Optional('default_response', default=''): str,
    sch.Optional('latency', default=0): sch.And(sch.Use(int), lambda n: 0 <= n),
    'requests': [{
        'in': str,
        'out': str,
        sch.Optional('delay', default=0): sch.And(sch.Use(int), lambda n: 0 <= n)
    }]
})

SCHEMA = sch.Schema({
    'interfaces': {
        sch.And(str, SAFE_STR_REG): TCP_SCHEMA
    },
    sch.Optional('vars'): {
        sch.And(str, SAFE_STR_REG): {
            'init': sch.Or(str, int),
            'type': str
        }
    }
})


def parse_file(file_path: str) -> 'Config':
    """Open the yaml file at the provided path and parse it.

    Generates a config object which is returned to the caller
    """

    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            return Config(SCHEMA.validate(config))

    except EnvironmentError as ex:
        raise ConfigIOError(
            "Unable to read file '{}'. {}".format(file_path, ex)) from ex
    except yaml.YAMLError as ex:
        raise InvalidConfig("Invalid configuration:\n{}".format(ex)) from ex


class Config:
    """Convert config to a class for easier use throughout Atticus

    The goal of this class is to reduce the amount having to update
    dictionary key accessors throughout Atticus everytime the Schema
    for the config changes. By having it stored as a class, changes
    may only require changing the Config class and not keys thoughout
    the entire program and all subprocesses. It would be great to use
    the dataclasses module in python but that was only added in 3.7
    """

    class Var:
        def __init__(self, name: str, var_config: Dict[str, str]) -> None:
            self._name = name
            self._init = var_config['init']
            self._type = var_config['type']

        @property
        def name(self) -> str:
            return self._name

        @property
        def initial_value(self) -> str:
            return self._init

        @property
        def value_type(self) -> str:
            return self._type

    class Interface:
        def __init__(self, name: str, props: Dict[Any, Any]) -> None:
            self._name = name
            self._properties = props

        @property
        def name(self) -> str:
            return self._name

        @property
        def props(self) -> Dict[Any, Any]:
            return self._properties

        @property
        def beak_type(self) -> str:
            return self._properties['type']

    def __init__(self, config: Dict[str, Any]) -> None:
        self._vars = {name: Config.Var(name, v_config)
                      for name, v_config in config.get('vars', {}).items()}
        self._interfaces = {name: Config.Interface(
            name, props) for name, props in config['interfaces'].items()}

    @property
    def interfaces(self) -> ValuesView['Config.Interface']:
        return self._interfaces.values()

    @property
    def vars(self) -> ValuesView['Config.Var']:
        return self._vars.values()
