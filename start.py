"""Portable convenience launcher: Python standard library only."""
import sys

if sys.version_info < (3, 10):
    print("SQL / LAB requires Python 3.10 or newer.")
    print("Install Python from https://www.python.org/downloads/ and try again.")
    raise SystemExit(1)

from server import main

if __name__ == "__main__":
    if "--open" not in sys.argv:
        sys.argv.append("--open")
    raise SystemExit(main() or 0)
