"""Provides a shell class for interactivly using Attiucs from the command line."""

import atexit
import cmd
import glob
import os
from typing import List

from .core import Atticus
from .errors import AtticusError


class Shell(cmd.Cmd):
    """Creates an interactive shell for controlling Atticus.

    This class inherits the Python cmd class in order to create a custom shell which
    calls the API methods from core.py
    """

    prompt = 'atticus> '
    intro = ("Welcome to Atticus. Type help or ? to list commands.")

    def __init__(self, *args) -> None:
        """Overrides Cmd constructor to construct an instance of Atticus."""

        self.atticus = Atticus()
        atexit.register(self.do_exit, None)
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

    def emptyline(self) -> None:
        pass

    def default(self, line: str) -> None:
        print('Unrecognized command:', line)

    def do_load(self, arg: str) -> None:
        """Load a mockingbird configuration from a YAML file."""

        try:
            mb_name = self.atticus.load(arg)
            print('Loaded', mb_name, 'from', arg)
        except AtticusError as ex:
            print(ex)

    def complete_load(self, _: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Autocomplete line with file paths for load command."""

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
            if arg:
                print(self.atticus.status(*arg.split()))
            else:
                print(self.atticus.status())
        except AtticusError as ex:
            print(ex)

    def complete_status(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for status command."""

        return self.autocomplete_mb(text)

    def do_start(self, arg: str) -> None:
        """Start the specified mockingbird config."""

        try:
            self.atticus.start(arg)
            print(arg, 'is now running')
        except AtticusError as ex:
            print(ex)

    def complete_start(self, text: str, _0: str, _1: int, _2: int) -> List[str]:
        """Autocomplete line with mockingbird names for start command."""

        return self.autocomplete_mb(text)

    def do_stop(self, arg: str) -> None:
        """Stop the specified mockingbird config."""

        try:
            self.atticus.stop(arg)
            print(arg, 'is now stopped')
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
        """ Returns """
        return [mb_name for mb_name in self.atticus._mb_processes if mb_name.startswith(text)]
