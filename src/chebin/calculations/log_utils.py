"""Helpers for printing large values without breaking a socket-backed stdout.

When the website runs as a service, stdout is an AF_UNIX SOCK_DGRAM socket to
journald rather than a file or a tty. A single write larger than the socket
send buffer cannot be split into datagrams, so it fails outright with
``OSError: [Errno 90] Message too long`` and turns a debug print into a 500 for
whichever request triggered it. The same write is harmless locally, where
stdout is a pipe or a tty, which is why these crashes only ever appear in
production and only for large study sets.

Printing whole leaf/ancestor/removed-node collections is what gets us there, so
route those through ``preview`` or ``describe`` instead of interpolating them
directly.
"""

MAX_PRINT_CHARS = 4000


def preview(value: object, limit: int = MAX_PRINT_CHARS) -> str:
    """Renders value as a string, truncated to limit characters."""

    text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated, {len(text)} chars total]"


def describe(collection, limit: int = MAX_PRINT_CHARS) -> str:
    """Renders a collection as its size followed by a truncated preview."""

    return f"{len(collection)} items: {preview(collection, limit)}"
