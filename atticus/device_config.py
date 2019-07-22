import typing

import yaml

from schema import And, Optional, Or, Regex, Schema, Use

IP_REG = Regex(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
SCHEMA = Schema({
    'name': str,
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

def parse_file(file_path: str) -> typing.Optional[typing.Dict]:
    """ Open the yaml file at the provided path and parse it to generate a config object. """

    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            return config if SCHEMA.is_valid(config) else None
    except EnvironmentError:
        print("Could not open file", file_path)
    except yaml.YAMLError:
        print("Invalid YAML", file_path)
    return None
