"""Provides a shell class for interactivly using Attiucs from the command line."""

import cmd
import glob
import os
from typing import Any, Dict, List

from .core import Atticus
from .errors import AtticusError


class Shell(cmd.Cmd):
    """Creates an interactive shell for controlling Atticus.

    This class inherits the Python cmd class in order to create a custom shell which
    calls the API methods from core.py
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

        Created with help from the Stack Overflow answer https://stackoverflow.com/a/27256663
        Answer by meffie
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

        Created with help from the Stack Overflow answer https://stackoverflow.com/a/27256663
        Answer by meffie
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
        """Load a mockingbird configuration from a YAML file."""

        mb_name, filename = args.split()
        try:
            self.atticus.load(mb_name, filename)
            print('Loaded', mb_name, 'from', filename)
        except AtticusError as ex:
            print(ex)

    def complete_load(self, _: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Autocomplete line with file paths for load command."""

        _, _, filename = line.split()

        if filename is None:
            return []

        return self.autocomplete_path(line, begidx, endidx)

    def do_unload(self, arg: str) -> None:
        """Unload a mockingbird configuration."""

        try:
            self.atticus.unload(arg)
            print(arg, 'unloaded')
        except AtticusError as ex:
            print(ex)

    def complete_unload(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for unload command."""

        return self.autocomplete_mb(text)

    def do_status(self, arg: str) -> None:
        """Print out the current status of loaded configurations."""

        try:
            statuses = self.atticus.status(*arg.split())
            Shell.print_statuses(statuses)

        except AtticusError as ex:
            print(ex)

    def complete_status(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for status command."""

        return self.autocomplete_mb(text)

    def do_start(self, arg: str) -> None:
        """Start the specified mockingbird config."""

        try:
            self.atticus.start(arg)
            print('Mockingbird', arg, 'is now running')
        except AtticusError as ex:
            print(ex)

    def complete_start(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for start command."""

        return self.autocomplete_mb(text)

    def do_stop(self, arg: str) -> None:
        """Stop the specified mockingbird config."""

        try:
            self.atticus.stop(arg)
            print('Mockingbird', arg, 'is now stopped')
        except AtticusError as ex:
            print(ex)

    def complete_stop(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for stop command."""

        return self.autocomplete_mb(text)

    def do_exit(self, _: str) -> bool:
        """Exit the atticus shell."""

        self.atticus.stop_all()
        print("Goodbye!")
        return True

    def autocomplete_mb(self, text: str) -> List[str]:
        """Returns all mockinbirds that have names that start with the given text."""
        return [mb_name for mb_name in self.atticus.status() if mb_name.startswith(text)]
