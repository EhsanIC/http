"""Shared HTTP response reading for the test suites.

A persistent (keep-alive) server does not close the socket after a response,
so tests must frame responses by Content-Length instead of waiting for EOF.
"""

import socket


def read_response(sock, buffer=b""):
    """Read exactly one HTTP response.

    Returns (raw_response_bytes, leftover_bytes). Leftover bytes belong to the
    next response and must be passed back in as ``buffer`` on the next call.
    """
    while b"\r\n\r\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            return buffer, b""
        buffer += chunk

    head, _, rest = buffer.partition(b"\r\n\r\n")

    length = None
    for line in head.split(b"\r\n")[1:]:
        name, _, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            try:
                length = int(value.strip())
            except ValueError:
                length = None

    if length is None:
        # No framing header (e.g. a 400): read until the server closes.
        while True:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            rest += chunk
        return head + b"\r\n\r\n" + rest, b""

    while len(rest) < length:
        chunk = sock.recv(4096)
        if not chunk:
            break
        rest += chunk

    return head + b"\r\n\r\n" + rest[:length], rest[length:]


def send_request(raw, host="localhost", port=4221, timeout=3):
    """Open a connection, send one request, read exactly one response."""
    with socket.create_connection((host, port), timeout=timeout) as client:
        client.sendall(raw)
        data, _ = read_response(client)
        return data
