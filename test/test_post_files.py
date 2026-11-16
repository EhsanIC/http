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
BOLD = "\033[1m"

HOST, PORT = "localhost", 4221

if len(sys.argv) < 2:
    print("usage: test_post_files.py <directory>")
    sys.exit(1)
DIRECTORY = sys.argv[1]

# files this test will create (cleaned up before + after)
CREATED = ["file_123", "abc_xyz", "empty_post", "bin_post"]

BINARY = b"\x00\x01\r\n\r\nbinary\xff"


def post(path: str, body: bytes) -> bytes:
    return (b"POST " + path.encode() + b" HTTP/1.1\r\n"
            b"Host: localhost:4221\r\n"
            b"User-Agent: test_post_files\r\n"
            b"Content-Type: application/octet-stream\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)


CREATED_RESPONSE = b"HTTP/1.1 201 Created\r\n\r\n"
NOT_FOUND = b"HTTP/1.1 404 Not Found\r\n\r\n"

TESTS = [
    {
        "name": "Create file (stage example)",
        "command": 'curl -v --data "12345" -H "Content-Type: application/octet-stream" http://localhost:4221/files/file_123',
        "request": post("/files/file_123", b"12345"),
        "expected": CREATED_RESPONSE,
        "verify_file": "file_123",
        "file_content": b"12345",
    },
    {
        "name": "Create file with random text body",
        "command": 'curl -v --data "hello world" -H "Content-Type: application/octet-stream" http://localhost:4221/files/abc_xyz',
        "request": post("/files/abc_xyz", b"hello world"),
        "expected": CREATED_RESPONSE,
        "verify_file": "abc_xyz",
        "file_content": b"hello world",
    },
    {
        "name": "Create file with empty body",
        "command": 'curl -v --data "" -H "Content-Type: application/octet-stream" http://localhost:4221/files/empty_post',
        "request": post("/files/empty_post", b""),
        "expected": CREATED_RESPONSE,
        "verify_file": "empty_post",
        "file_content": b"",
    },
    {
        "name": "Create binary file (body contains \\r\\n\\r\\n)",
        "command": 'curl -v --data-binary "\\x00\\x01\\r\\n\\r\\nbinary\\xff" -H "Content-Type: application/octet-stream" http://localhost:4221/files/bin_post',
        "request": post("/files/bin_post", BINARY),
        "expected": CREATED_RESPONSE,
        "verify_file": "bin_post",
        "file_content": BINARY,
    },
    {
        "name": "Overwrite existing file",
        "command": 'curl -v --data "replaced" -H "Content-Type: application/octet-stream" http://localhost:4221/files/foo',
        "request": post("/files/foo", b"replaced"),
        "expected": CREATED_RESPONSE,
        "verify_file": "foo",
        "file_content": b"replaced",
    },
    {
        "name": "Path traversal must not escape the directory",
        "command": "curl -v --path-as-is --data \"evil\" http://localhost:4221/files/../app/main.py",
        "request": post("/files/../app/main.py", b"evil"),
        "expected": NOT_FOUND,
    },
    {
        "name": "/files/ with no filename",
        "command": 'curl -v --data "data" http://localhost:4221/files/',
        "request": post("/files/", b"data"),
        "expected": NOT_FOUND,
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


def cleanup():
    os.makedirs(DIRECTORY, exist_ok=True)
    # re-create "foo" so the overwrite test always starts from a known state,
    # and delete files the POST tests create so re-runs are deterministic
    with open(os.path.join(DIRECTORY, "foo"), "wb") as f:
        f.write(b"Hello, World!")
    for name in CREATED:
        try:
            os.remove(os.path.join(DIRECTORY, name))
        except OSError:
            pass


def read_file(name: str) -> bytes:
    with open(os.path.join(DIRECTORY, name), "rb") as f:
        return f.read()


def main():
    cleanup()
    failed = 0
    for t in TESTS:
        print(f"{CYAN}Test:{RESET}     {t['name']}")
        print(f"{CYAN}Command:{RESET}  {DIM}{t['command']}{RESET}")
        try:
            actual = send_request(t["request"])
        except Exception as e:
            actual = f"ERROR: {e}".encode()
        print(f"{CYAN}Output:{RESET}   {actual!r}")

        passed = actual == t["expected"]

        if passed and "verify_file" in t:
            try:
                content = read_file(t["verify_file"])
            except OSError as e:
                content = f"ERROR: {e}".encode()
            print(f"{CYAN}On disk:{RESET}  {content!r}")
            if content != t["file_content"]:
                passed = False
                print(f"{CYAN}Wanted:{RESET}   {t['file_content']!r}")

        if passed:
            print(f"{CYAN}Result:{RESET}   {GREEN}{BOLD}PASS{RESET}\n")
        else:
            failed += 1
            print(f"{CYAN}Expected:{RESET} {t['expected']!r}")
            print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")

    # restore the overwrite victim for the GET tests in test_files.py
    with open(os.path.join(DIRECTORY, "foo"), "wb") as f:
        f.write(b"Hello, World!")

    color = RED if failed else GREEN
    print(f"{color}{BOLD}{len(TESTS) - failed}/{len(TESTS)} passed{RESET}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
