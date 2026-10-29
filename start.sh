#!/bin/sh
# Run from any directory. No environment, packages, or build step needed.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    exec python3 start.py "$@"
elif command -v python >/dev/null 2>&1; then
    exec python start.py "$@"
else
    printf '%s\n' 'Python 3.10 or newer is required: https://www.python.org/downloads/' >&2
    exit 1
fi
