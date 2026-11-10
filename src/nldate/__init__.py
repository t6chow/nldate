"""Natural-language date parsing."""

import sys

from nldate.parser import parse

__all__ = ["main", "parse"]


def main() -> None:
    """Command-line entry point: print the date for each argument."""
    for arg in sys.argv[1:]:
        print(parse(arg))
