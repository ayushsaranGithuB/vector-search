"""Check if a TCP port is available.

Usage: python check_port.py [port]

Exits with code 0 if the port is free, 1 if it's already in use.
"""

import socket
import sys

DEFAULT_PORT = 8000


def check_port(host: str, port: int) -> bool:
    """Return True if the port is available (not in use)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        return result != 0


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    if check_port("127.0.0.1", port):
        print(f"[OK] Port {port} is available.")
        sys.exit(0)
    else:
        print(
            f"ERROR: Port {port} is already in use.\n"
            f"       Is the server already running?\n"
            f"       Stop the existing process first, or use a different port.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
