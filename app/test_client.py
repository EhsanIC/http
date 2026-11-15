import os
import socket
import sys

# Enable ANSI escape codes on Windows terminals
if os.name == "nt":
    os.system("")

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
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
]


def send_request(raw: bytes) -> bytes:
    with socket.create_connection((HOST, PORT), timeout=3) as client:
        client.sendall(raw)
        data = b""
        while True:                    # read until the server closes
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
        return data


def main():
    failed = 0
    for t in TESTS:
        print(f"{CYAN}Test:{RESET}     {t['name']}")
        print(f"{CYAN}Command:{RESET}  {DIM}{t['command']}{RESET}")
        try:
            actual = send_request(t["request"])
        except Exception as e:
            actual = f"ERROR: {e}".encode()
        print(f"{CYAN}Output:{RESET}   {actual!r}")
        if actual == t["expected"]:
            print(f"{CYAN}Result:{RESET}   {GREEN}{BOLD}PASS{RESET}\n")
        else:
            failed += 1
            print(f"{CYAN}Expected:{RESET} {t['expected']!r}")
            print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")
    if failed:
        print(f"{RED}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    else:
        print(f"{GREEN}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
