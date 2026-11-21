import gzip
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

EXPECT_ECHO = {
    "contains": [b"HTTP/1.1 200 OK", b"Content-Type: text/plain", b"Content-Length: 6"],
    "body": b"banana",
}
EXPECT_UA = {
    "contains": [b"HTTP/1.1 200 OK", b"Content-Type: text/plain", b"Content-Length: 25"],
    "body": b"blueberry/apple-blueberry",
}

REQ_ECHO = b"GET /echo/banana HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
REQ_UA = (b"GET /user-agent HTTP/1.1\r\nHost: localhost:4221\r\n"
          b"User-Agent: blueberry/apple-blueberry\r\n\r\n")

TESTS = [
    {
        "name": "Two sequential requests reuse one connection",
        "command": ('curl --http1.1 -v http://localhost:4221/echo/banana '
                    '--next http://localhost:4221/user-agent -H "User-Agent: blueberry/apple-blueberry"'),
        "requests": [REQ_ECHO, REQ_UA],
        "expects": [EXPECT_ECHO, EXPECT_UA],
    },
    {
        "name": "Connection: close is honored",
        "command": 'curl -v -H "Connection: close" http://localhost:4221/echo/banana',
        "requests": [b"GET /echo/banana HTTP/1.1\r\nHost: localhost:4221\r\nConnection: close\r\n\r\n"],
        "expects": [EXPECT_ECHO],
        "expect_closed": True,
    },
    {
        "name": "Pipelined requests in a single send",
        "command": 'printf "GET /echo/banana HTTP/1.1\\r\\n\\r\\nGET /user-agent HTTP/1.1\\r\\n\\r\\n" | nc localhost 4221',
        "requests": [REQ_ECHO, REQ_UA],
        "pipeline": True,
        "expects": [EXPECT_ECHO, EXPECT_UA],
    },
    {
        "name": "Encoding is decided per request, not per connection",
        "command": ('curl --http1.1 -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/banana '
                    '--next http://localhost:4221/echo/banana'),
        "requests": [
            b"GET /echo/banana HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: gzip\r\n\r\n",
            REQ_ECHO,
        ],
        "expects": [
            {"contains": [b"HTTP/1.1 200 OK", b"Content-Encoding: gzip"], "gzip_body": b"banana"},
            EXPECT_ECHO,
        ],
    },
]


def verify(exp, raw):
    problems = []
    head, sep, body = raw.partition(b"\r\n\r\n")
    if not sep:
        return [f"no complete response (got {raw!r})"]

    if "exact" in exp and raw != exp["exact"]:
        problems.append(f"expected {exp['exact']!r}, got {raw!r}")
    for needle in exp.get("contains", []):
        if needle not in raw:
            problems.append(f"missing {needle!r}")
    for needle in exp.get("not_contains", []):
        if needle in raw:
            problems.append(f"unexpected {needle!r}")
    if "body" in exp and body != exp["body"]:
        problems.append(f"body {body!r} != {exp['body']!r}")
    if "gzip_body" in exp:
        try:
            plain = gzip.decompress(body)
        except OSError as e:
            problems.append(f"body is not valid gzip: {e}")
        else:
            if plain != exp["gzip_body"]:
                problems.append(f"decompressed body {plain!r} != {exp['gzip_body']!r}")
    return problems


def run_test(t):
    """Drive one TCP connection through the test's requests. Returns (problems, outputs)."""
    problems = []
    outputs = []

    try:
        sock = socket.create_connection((HOST, PORT), timeout=3)
    except Exception as e:
        return [f"could not connect: {e}"], outputs

    try:
        buffer = b""

        if t.get("pipeline"):
            sock.sendall(b"".join(t["requests"]))
            for i, exp in enumerate(t["expects"]):
                raw, buffer = helpers.read_response(sock, buffer)
                outputs.append(raw)
                problems += verify(exp, raw)
        else:
            for i, req in enumerate(t["requests"]):
                try:
                    sock.sendall(req)
                except OSError as e:
                    problems.append(f"request {i + 1} could not be sent (connection closed?): {e}")
                    break
                raw, buffer = helpers.read_response(sock, buffer)
                outputs.append(raw)
                problems += verify(t["expects"][i], raw)

        if t.get("expect_closed") and not problems:
            sock.settimeout(2)
            try:
                rest = sock.recv(4096)
            except socket.timeout:
                problems.append("server kept the connection open despite Connection: close")
            else:
                if rest:
                    problems.append(f"unexpected extra data after response: {rest!r}")
    except Exception as e:
        problems.append(f"error: {e}")
    finally:
        sock.close()

    return problems, outputs


ORDER = {id(t): i for i, t in enumerate(TESTS)}

# shared results file — client_test.ps1 collects all suites from it at the end
RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results.txt")


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
        problems, outputs = run_test(t)
        for i, out in enumerate(outputs):
            print(f"{CYAN}Response {i + 1}:{RESET} {out!r}")

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
