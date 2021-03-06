"""
Copyright (c) 2020 Nathan Telles

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import cmd
import glob
import os
from typing import Any, Dict, List

from .core import Atticus
from .errors import AtticusAPIError


class Shell(cmd.Cmd):
    """Creates an interactive shell for controlling Atticus.

    This class inherits the Python cmd class in order to create a custom shell
    which calls the API methods from core.py
    """

    prompt = 'atticus> '
    intro = ("Welcome to Atticus. Type help or ? to list commands.")

    def __init__(self, *args: Any) -> None:
        """Overrides Cmd constructor to construct an instance of Atticus."""

        self.atticus = Atticus()
        super().__init__(*args)

    @staticmethod
    def autocomplete_path(line: str, begidx: int, endidx: int) -> List[str]:
        """Autocomplete file path.

        Created with help from the Stack Overflow answer by meffie
        https://stackoverflow.com/a/27256663
        """

        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return []

        fixed = line[before_arg+1:begidx]
        arg = line[before_arg+1:endidx]
        pattern = arg + '*'

        completions = []
        for path in glob.glob(pattern):
            path = Shell.append_slash_if_dir(path)
            completions.append(path.replace(fixed, "", 1))
        return completions

    @staticmethod
    def append_slash_if_dir(path: str) -> str:
        """Append a slash to path name if the path is a directory

        Created with help from the Stack Overflow answer by meffie
        https://stackoverflow.com/a/27256663
        """

        if path and os.path.isdir(path) and path[-1] != os.sep:
            return path + os.sep

        return path

    @staticmethod
    def print_statuses(statuses: Dict) -> None:
        """Pretty print mockingbird statuses."""

        header = str.format("{:<20} {:<15}", 'Mockingbird', 'Status')
        print()
        print(header)
        print('-' * 36)
        for mb_name, stat in statuses.items():
            row = str.format("{:<20} {:<15}", mb_name, stat['status'])
            print(row)
        print()

    def emptyline(self) -> bool:
        pass

    def default(self, line: str) -> bool:
        print('Unrecognized command:', line)
        return False

    def do_load(self, args: str) -> None:
        """Load a mockingbird configuration from a YAML file.

        Usage: load mb_name config_file_path"""

        split_args = args.split()
        if len(split_args) != 2:
            self.invalid_command('load')
            return

        mb_name, filename = split_args

        try:
            self.atticus.load(mb_name, filename)
            print('Loaded', mb_name, 'from', filename)
        except AtticusAPIError as ex:
            print(ex)

    def complete_load(self, _: str, line: str, beg: int, end: int) -> List[str]:
        """Autocomplete line with file paths for load command."""

        _, _, filename = line.split()

        if filename is None:
            return []

        return self.autocomplete_path(line, beg, end)

    def do_unload(self, arg: str) -> None:
        """Unload a mockingbird configuration.\nUsage: unload mb_name"""

        if not arg:
            self.invalid_command('unload')
            return

        try:
            self.atticus.unload(arg)
            print(arg, 'unloaded')
        except AtticusAPIError as ex:
            print(ex)

    def complete_unload(self, txt: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for unload command."""

        return self.autocomplete_mb(txt)

    def do_status(self, arg: str) -> None:
        """Print out the current status of loaded configurations.

        Usage: status [mb_name ...]
        """

        try:
            statuses = self.atticus.status(*arg.split())
            Shell.print_statuses(statuses)

        except AtticusAPIError as ex:
            print(ex)

    def complete_status(self, txt: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for status command."""

        return self.autocomplete_mb(txt)

    def do_start(self, arg: str) -> None:
        """Start the specified mockingbird config.\nUsage: start mb_name"""

        if not arg:
            self.invalid_command('start')
            return

        try:
            self.atticus.start(arg)
            print('Mockingbird', arg, 'is now running')
        except AtticusAPIError as ex:
            print(ex)

    def complete_start(self, txt: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for start command."""

        return self.autocomplete_mb(txt)

    def do_stop(self, arg: str) -> None:
        """Stop the specified mockingbird config.\nUsage: stop mb_name"""

        if not arg:
            self.invalid_command('stop')
            return

        try:
            self.atticus.stop(arg)
            print('Mockingbird', arg, 'is now stopped')
        except AtticusAPIError as ex:
            print(ex)

    def complete_stop(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for stop command."""

        return self.autocomplete_mb(text)

    def do_exit(self, _: str) -> bool:
        """Exit the atticus shell."""

        self.atticus.stop_all()
        print("\nGoodbye!")
        return True

    def autocomplete_mb(self, txt: str) -> List[str]:
        """Returns all mockinbirds that have names starting with txt."""
        return [name for name in self.atticus.status() if name.startswith(txt)]

    def invalid_command(self, command: str) -> None:
        print("Invalid use of command", command)
        print()
        self.do_help(command)
