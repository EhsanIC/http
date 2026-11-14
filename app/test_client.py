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
        "name": "Respond with 200",
        "command": "curl -v http://localhost:4221",   # shown in the log only
        "request": b"GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": b"HTTP/1.1 200 OK\r\n\r\n",
    },
    # add more tests here
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