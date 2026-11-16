import os
import socket
import sys

if os.name == "nt":
    os.system("")

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
BOLD = "\033[1m"

HOST, PORT = "127.0.0.1", 4221

if len(sys.argv) < 2:
    print("usage: test_files.py <directory>")
    sys.exit(1)
DIRECTORY = sys.argv[1]

BINARY = b"\x00\x01\r\n\r\nbinary\xff"


def make_files():
    os.makedirs(DIRECTORY, exist_ok=True)
    with open(os.path.join(DIRECTORY, "foo"), "wb") as f:
        f.write(b"Hello, World!")
    with open(os.path.join(DIRECTORY, "empty"), "wb") as f:
        f.write(b"")
    with open(os.path.join(DIRECTORY, "data.bin"), "wb") as f:
        f.write(BINARY)


def ok(body: bytes) -> bytes:
    return (b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)


NOT_FOUND = b"HTTP/1.1 404 Not Found\r\n\r\n"

TESTS = [
    {
        "name": "Existing file",
        "command": "curl -i http://localhost:4221/files/foo",
        "request": b"GET /files/foo HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": ok(b"Hello, World!"),
    },
    {
        "name": "Missing file",
        "command": "curl -i http://localhost:4221/files/non_existant_file",
        "request": b"GET /files/non_existant_file HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": NOT_FOUND,
    },
    {
        "name": "Empty file",
        "command": "curl -i http://localhost:4221/files/empty",
        "request": b"GET /files/empty HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": ok(b""),
    },
    {
        "name": "Binary file (contains \\r\\n\\r\\n and a 0xff byte)",
        "command": "curl -i http://localhost:4221/files/data.bin",
        "request": b"GET /files/data.bin HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": ok(BINARY),
    },
    {
        "name": "Path traversal must not escape the directory",
        "command": "curl -i --path-as-is http://localhost:4221/files/../app/main.py",
        "request": b"GET /files/../app/main.py HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": NOT_FOUND,
    },
    {
        "name": "/files/ with no filename",
        "command": "curl -i http://localhost:4221/files/",
        "request": b"GET /files/ HTTP/1.1\r\nHost: localhost:4221\r\n\r\n",
        "expected": NOT_FOUND,
    },
]


def send_request(raw: bytes) -> bytes:
    with socket.create_connection((HOST, PORT), timeout=3) as client:
        client.sendall(raw)
        data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
        return data


def main():
    make_files()
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
    color = RED if failed else GREEN
    print(f"{color}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()