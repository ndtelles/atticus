"""Provides the entry-point to Atticus when run from the command line."""

from .shell import Shell

if __name__ == '__main__':
    Shell().cmdloop()
