"""Connection: close stage.

A request without the header keeps the connection alive; a request carrying
``Connection: close`` must be echoed back with the same header and then the
TCP connection must be closed by the server.
"""

import os
import socket
import sys

import helpers

# Enable ANSI escape codes on Windows terminals
if os.name == "nt":
    os.system("")

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"

HOST, PORT = "localhost", 4221

# shared results file — client_test.ps1 collects all suites from it at the end
RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results.txt")


# requests ///////////////////////////////////////////////////////////////////

def req_echo(value, connection=None):
    head = f"GET /echo/{value} HTTP/1.1\r\nHost: localhost:4221\r\n"
    if connection:
        head += f"Connection: {connection}\r\n"
    return (head + "\r\n").encode()


def req_root(connection=None):
    head = "GET / HTTP/1.1\r\nHost: localhost:4221\r\n"
    if connection:
        head += f"Connection: {connection}\r\n"
    return (head + "\r\n").encode()


def connect(timeout=5):
    return socket.create_connection((HOST, PORT), timeout=timeout)


# verification ////////////////////////////////////////////////////////////////

def expect(exp, raw, label, problems):
    head, sep, body = raw.partition(b"\r\n\r\n")
    if not sep:
        problems.append(f"{label}: no complete response (got {raw!r})")
        return

    if b"HTTP/1.1 200 OK" not in head:
        problems.append(f"{label}: expected 200 OK, got {head[:40]!r}")

    has_close = b"connection: close" in head.lower()
    if exp.get("close_header") is True and not has_close:
        problems.append(f"{label}: response is missing 'Connection: close'")
    if exp.get("close_header") is False and has_close:
        problems.append(f"{label}: unexpected 'Connection: close' on a keep-alive response")

    if "body" in exp and body != exp["body"]:
        problems.append(f"{label}: body {body!r} != {exp['body']!r}")


def is_closed(sock, timeout=2.0):
    """True when the server actually closed its end of the connection."""
    sock.settimeout(timeout)
    try:
        return sock.recv(4096) == b""
    except socket.timeout:
        return False
    except OSError:
        return True   # a reset also means "closed"


# tests ///////////////////////////////////////////////////////////////////////

def test_keep_alive_by_default():
    """No Connection header: the socket stays open for another request."""
    problems = []
    sock = None
    try:
        sock = connect()
        sock.sendall(req_echo("orange"))
        raw, buf = helpers.read_response(sock, b"")
        expect({"body": b"orange", "close_header": False}, raw, "request 1 (no header)", problems)

        sock.sendall(req_echo("banana"))
        raw, buf = helpers.read_response(sock, buf)
        expect({"body": b"banana", "close_header": False}, raw, "request 2 on the same socket", problems)
    except Exception as e:
        problems.append(f"error: {e}")
    finally:
        if sock is not None:
            sock.close()
    return problems


def test_connection_close_on_echo():
    """Connection: close on a text response: header echoed, then EOF."""
    problems = []
    sock = None
    try:
        sock = connect()
        sock.sendall(req_echo("grape", connection="close"))
        raw, _ = helpers.read_response(sock, b"")
        expect({"body": b"grape", "close_header": True}, raw, "echo with Connection: close", problems)
        if not is_closed(sock):
            problems.append("server kept the connection open after 'Connection: close'")
    except Exception as e:
        problems.append(f"error: {e}")
    finally:
        if sock is not None:
            sock.close()
    return problems


def test_connection_close_on_empty_body():
    """Connection: close on 'GET /' (no body to frame): header echoed, then EOF."""
    problems = []
    sock = None
    try:
        sock = connect()
        sock.sendall(req_root(connection="close"))
        raw, _ = helpers.read_response(sock, b"")
        expect({"close_header": True}, raw, "GET / with Connection: close", problems)
        if not is_closed(sock):
            problems.append("server kept the connection open after 'Connection: close'")
    except Exception as e:
        problems.append(f"error: {e}")
    finally:
        if sock is not None:
            sock.close()
    return problems


def test_exact_tester_flow():
    """The stage's own curl line: keep-alive request, then a closing one."""
    problems = []
    sock = None
    try:
        sock = connect()

        sock.sendall(req_echo("orange"))
        raw, buf = helpers.read_response(sock, b"")
        expect({"body": b"orange", "close_header": False}, raw, "first request (keep-alive)", problems)

        sock.sendall(req_root(connection="close"))
        raw, _ = helpers.read_response(sock, buf)
        expect({"close_header": True}, raw, "second request (Connection: close)", problems)

        if not is_closed(sock):
            problems.append("server kept the connection open after the closing request")
    except Exception as e:
        problems.append(f"error: {e}")
    finally:
        if sock is not None:
            sock.close()
    return problems


TESTS = [
    {
        "name": "Regular request keeps the connection open",
        "command": 'curl --http1.1 -v http://localhost:4221/echo/orange --next http://localhost:4221/echo/banana',
        "run": test_keep_alive_by_default,
    },
    {
        "name": "Connection: close on /echo is echoed and closes the socket",
        "command": 'curl -v -H "Connection: close" http://localhost:4221/echo/grape',
        "run": test_connection_close_on_echo,
    },
    {
        "name": "Connection: close on / (raw 200) is echoed and closes the socket",
        "command": 'curl -v -H "Connection: close" http://localhost:4221/',
        "run": test_connection_close_on_empty_body,
    },
    {
        "name": "Exact tester flow: keep-alive request, then Connection: close",
        "command": 'curl --http1.1 -v http://localhost:4221/echo/orange --next http://localhost:4221/ -H "Connection: close"',
        "run": test_exact_tester_flow,
    },
]


def append_results(passed_names, failed_names):
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        for name in passed_names:
            f.write(f"PASS\t{name}\n")
        for name in failed_names:
            f.write(f"FAIL\t{name}\n")


def main():
    failed = 0
    passed_list = []
    failed_list = []

    for t in TESTS:
        print(f"{CYAN}Test:{RESET}     {t['name']}")
        print(f"{CYAN}Command:{RESET}  {DIM}{t['command']}{RESET}")

        try:
            problems = t["run"]()
        except Exception as e:
            problems = [f"error: {e}"]

        if problems:
            failed += 1
            failed_list.append(t["name"])
            for p in problems:
                print(f"{CYAN}Problem:{RESET}  {p}")
            print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")
        else:
            print(f"{CYAN}Result:{RESET}   {GREEN}{BOLD}PASS{RESET}\n")
            passed_list.append(t["name"])

    append_results(passed_list, failed_list)
    color = RED if failed else GREEN
    print(f"{color}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
