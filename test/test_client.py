import os
import socket
import sys
import threading
import gzip

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

TESTS = [
    {
        "name": "Respond with 200 on /",
        "command": "curl -v http://localhost:4221",
        "request": b"GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\n\r\n",
    },
    {
        "name": "Respond with 404 on random path",
        "command": "curl -v http://localhost:4221/abcdefg",
        "request": b"GET /abcdefg HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 404 Not Found\r\n\r\n",
    },
    {
        "name": "Respond with 404 on /index.html",
        "command": "curl -v http://localhost:4221/index.html",
        "request": b"GET /index.html HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/7.64.1\r\nAccept: */*\r\n\r\n",
        "expected": b"HTTP/1.1 404 Not Found\r\n\r\n",
    },
    {
        "name": "Respond with 200 on / (with extra headers)",
        "command": "curl -v http://localhost:4221",
        "request": b"GET / HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/7.64.1\r\nAccept: */*\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\n\r\n",
    },
    {
        "name": "Echo a short string",
        "command": "curl -v http://localhost:4221/echo/abc",
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\nabc",
    },
    {
        "name": "Echo a longer string",
        "command": "curl -v http://localhost:4221/echo/hello-world",
        "request": b"GET /echo/hello-world HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/7.64.1\r\nAccept: */*\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 11\r\n\r\nhello-world",
    },
    {
        "name": "Echo a single character",
        "command": "curl -v http://localhost:4221/echo/x",
        "request": b"GET /echo/x HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 1\r\n\r\nx",
    },
    {
        "name": "Echo digits and underscores",
        "command": "curl -v http://localhost:4221/echo/raspberry_123",
        "request": b"GET /echo/raspberry_123 HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nraspberry_123",
    },
    {
        "name": "User-Agent basic",
        "command": 'curl -v --header "User-Agent: foobar/1.2.3" http://localhost:4221/user-agent',
        "request": b"GET /user-agent HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: foobar/1.2.3\r\nAccept: */*\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 12\r\n\r\nfoobar/1.2.3",
    },
    {
        "name": "User-Agent as last header",
        "command": 'curl -v --header "User-Agent: mango/9.9" http://localhost:4221/user-agent',
        "request": b"GET /user-agent HTTP/1.1\r\nHost: localhost:4221\r\nAccept: */*\r\nUser-Agent: mango/9.9\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nmango/9.9",
    },
    {
        "name": "User-Agent as first header",
        "command": 'curl -v --header "User-Agent: blueberry/1.0" http://localhost:4221/user-agent',
        "request": b"GET /user-agent HTTP/1.1\r\nUser-Agent: blueberry/1.0\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nblueberry/1.0",
    },
    {
        "name": "User-Agent with spaces in value",
        "command": 'curl -v --header "User-Agent: Mozilla/5.0 (X11; Linux)" http://localhost:4221/user-agent',
        "request": b"GET /user-agent HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: Mozilla/5.0 (X11; Linux)\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 24\r\n\r\nMozilla/5.0 (X11; Linux)",
    },
    {
        "name": "User-Agent header name in lowercase",
        "command": 'curl -v --header "user-agent: apple/2.0" http://localhost:4221/user-agent',
        "request": b"GET /user-agent HTTP/1.1\r\nHost: localhost:4221\r\nuser-agent: apple/2.0\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\napple/2.0",
    },
    # --- compression: Accept-Encoding / Content-Encoding ---
    {
        "name": "Compression: gzip requested adds Content-Encoding",
        "command": 'curl -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/abc',
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/7.81.0\r\nAccept: */*\r\nAccept-Encoding: gzip\r\n\r\n",
        "must_contain": [b"HTTP/1.1 200 OK", b"Content-Encoding: gzip", b"Content-Type: text/plain"],
        "must_not_contain": [b"\r\n\r\nabc"],
    },
    {
        "name": "Compression: invalid encoding gets no Content-Encoding",
        "command": 'curl -v -H "Accept-Encoding: invalid-encoding" http://localhost:4221/echo/abc',
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: invalid-encoding\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\nabc",
        "must_not_contain": [b"Content-Encoding"],
    },
    {
        "name": "Compression: gzip among multiple encodings",
        "command": 'curl -v -H "Accept-Encoding: gzip, deflate" http://localhost:4221/echo/abc',
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: gzip, deflate\r\n\r\n",
        "must_contain": [b"HTTP/1.1 200 OK", b"Content-Encoding: gzip"],
        "must_not_contain": [b"\r\n\r\nabc"],
    },
    {
        "name": "Compression: gzip mixed with invalid encodings",
        "command": 'curl -v -H "Accept-Encoding: invalid-encoding-1, gzip, invalid-encoding-2" http://localhost:4221/echo/abc',
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: invalid-encoding-1, gzip, invalid-encoding-2\r\n\r\n",
        "must_contain": [b"HTTP/1.1 200 OK", b"Content-Encoding: gzip", b"Content-Type: text/plain"],
        "must_not_contain": [b"\r\n\r\nabc"],
    },
    {
        "name": "Compression: only invalid encodings gets no Content-Encoding",
        "command": 'curl -v -H "Accept-Encoding: invalid-encoding-1, invalid-encoding-2" http://localhost:4221/echo/abc',
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: invalid-encoding-1, invalid-encoding-2\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\nabc",
        "must_not_contain": [b"Content-Encoding"],
    },
    # --- gzip compression: the body must really be compressed ---
    {
        "name": "Compression: gzip body is actually compressed",
        "command": 'curl -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/abc | hexdump -C',
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\nUser-Agent: curl/7.81.0\r\nAccept: */*\r\nAccept-Encoding: gzip\r\n\r\n",
        "gzip_body": b"abc",
    },
    {
        "name": "Compression: gzip body for a longer string",
        "command": 'curl -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/hello-world | hexdump -C',
        "request": b"GET /echo/hello-world HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: gzip\r\n\r\n",
        "gzip_body": b"hello-world",
    },
    {
        "name": "Compression: gzip body for repeated text",
        "command": 'curl -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/aaaaaaaaaaaaaaaaaaaa | hexdump -C',
        "request": b"GET /echo/aaaaaaaaaaaaaaaaaaaa HTTP/1.1\r\nHost: localhost:4221\r\nAccept-Encoding: gzip\r\n\r\n",
        "gzip_body": b"aaaaaaaaaaaaaaaaaaaa",
    },
    {
        "name": "Compression: no Accept-Encoding gets no Content-Encoding",
        "command": "curl -v http://localhost:4221/echo/abc",
        "request": b"GET /echo/abc HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\nabc",
        "must_not_contain": [b"Content-Encoding"],
    },
]


def send_request(raw: bytes) -> bytes:
    """Send one request and read exactly one response (Content-Length framed)."""
    return helpers.send_request(raw, HOST, PORT)


def run_test(t, barrier, results):
    barrier.wait()                     # all tests released at the same moment

    try:
        data = send_request(t["request"])
    except Exception as e:
        data = f"ERROR: {e}".encode()
    results.append({"test": t, "data": data})


ORDER = {id(t): i for i, t in enumerate(TESTS)}


def check(t, data):
    """Exact match when 'expected' is set, plus contains / not-contains rules."""
    if "expected" in t and data != t["expected"]:
        return False
    for needle in t.get("must_contain", []):
        if needle not in data:
            return False
    for needle in t.get("must_not_contain", []):
        if needle in data:
            return False
    return True


def explain_failure(t, data):
    """Print what the test wanted when it fails."""
    if "expected" in t:
        print(f"{CYAN}Expected:{RESET} {t['expected']!r}")
    for needle in t.get("must_contain", []):
        if needle not in data:
            print(f"{CYAN}Missing:{RESET}  {needle!r}")
    for needle in t.get("must_not_contain", []):
        if needle in data:
            print(f"{CYAN}Unexpected:{RESET} {needle!r}")


def gzip_problems(t, data):
    """Verify a response that must carry a real gzip-compressed body."""
    problems = []
    head, sep, body = data.partition(b"\r\n\r\n")
    if not sep:
        return ["response has no header/body separator"]

    header_lines = head.split(b"\r\n")
    if header_lines[0] != b"HTTP/1.1 200 OK":
        problems.append(f"status line is {header_lines[0]!r}")
    if b"Content-Type: text/plain" not in header_lines[1:]:
        problems.append("missing Content-Type: text/plain")
    if b"Content-Encoding: gzip" not in header_lines[1:]:
        problems.append("missing Content-Encoding: gzip")

    length = None
    for line in header_lines[1:]:
        name, _, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            try:
                length = int(value.strip())
            except ValueError:
                problems.append(f"Content-Length is not a number: {value!r}")
    if length is None:
        problems.append("missing Content-Length")
    elif length != len(body):
        problems.append(f"Content-Length {length} != actual body size {len(body)}")

    try:
        plain = gzip.decompress(body)
    except OSError as e:
        problems.append(f"body is not valid gzip: {e}")
    else:
        if plain != t["gzip_body"]:
            problems.append(f"decompressed body {plain!r} != {t['gzip_body']!r}")

    return problems


# shared results file — client_test.ps1 collects all suites from it at the end
RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results.txt")


def append_results(passed_names, failed_names):
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        for name in passed_names:
            f.write(f"PASS\t{name}\n")
        for name in failed_names:
            f.write(f"FAIL\t{name}\n")


def main():
    n = len(TESTS)
    barrier = threading.Barrier(n)
    results = []
    threads = [threading.Thread(target=run_test, args=(t, barrier, results)) for t in TESTS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # print in the original TESTS order, so output is deterministic
    failed = 0
    passed_list = []
    failed_list = []
    for r in sorted(results, key=lambda r: ORDER[id(r["test"])]):
        t = r["test"]
        print(f"{CYAN}Test:{RESET}     {t['name']}")
        print(f"{CYAN}Command:{RESET}  {DIM}{t['command']}{RESET}")
        print(f"{CYAN}Output:{RESET}   {r['data']!r}")
        if check(t, r["data"]):
            problems = gzip_problems(t, r["data"]) if "gzip_body" in t else []
            if problems:
                failed += 1
                failed_list.append(t["name"])
                for p in problems:
                    print(f"{CYAN}Problem:{RESET}  {p}")
                print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")
            else:
                print(f"{CYAN}Result:{RESET}   {GREEN}{BOLD}PASS{RESET}\n")
                passed_list.append(t["name"])
        else:
            failed += 1
            failed_list.append(t["name"])
            explain_failure(t, r["data"])
            print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")

    append_results(passed_list, failed_list)
    if failed:
        print(f"{RED}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    else:
        print(f"{GREEN}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
