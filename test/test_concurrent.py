import os
import socket
import sys
import time

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

HOST, PORT = "127.0.0.1", 4221
EXPECTED = b"HTTP/1.1 200 OK\r\n\r\n"
N = 3            # number of clients sent while the idle one blocks
MAX_SECONDS = 1  # a threaded server answers well under this


def run_client(i, results):
    name = f"Concurrent client {i + 1} is served while another is idle"
    command = '(printf "GET / HTTP/1.1\\r\\n\\r\\n") | nc localhost 4221'

    print(f"{CYAN}Test:{RESET}     {name}")
    print(f"{CYAN}Command:{RESET}  {DIM}{command}{RESET}")

    start = time.time()
    try:
        c = socket.create_connection((HOST, PORT), timeout=2)
        c.sendall(b"GET / HTTP/1.1\r\n\r\n")
        try:
            data = c.recv(4096)
        except socket.timeout:
            data = b""
        c.close()
    except Exception as e:
        data = f"ERROR: {e}".encode()
    elapsed = time.time() - start

    print(f"{CYAN}Output:{RESET}   {data!r} {DIM}({elapsed:.2f}s){RESET}")

    if data == EXPECTED and elapsed < MAX_SECONDS:
        print(f"{CYAN}Result:{RESET}   {GREEN}{BOLD}PASS{RESET}\n")
        results.append(True)
    else:
        print(f"{CYAN}Expected:{RESET} {EXPECTED!r} {DIM}(in under {MAX_SECONDS}s){RESET}")
        print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")
        results.append(False)


def main():
    print(f"{YELLOW}Opening an idle connection that sends nothing...{RESET}\n")

    # silent client connects first and blocks a sequential server in recv()
    try:
        idle = socket.create_connection((HOST, PORT), timeout=5)
    except Exception as e:
        print(f"{RED}{BOLD}Could not connect to the server: {e}{RESET}")
        sys.exit(1)

    time.sleep(0.5)

    results = []
    for i in range(N):
        run_client(i, results)

    idle.close()

    passed = sum(results)
    color = GREEN if passed == N else RED
    print(f"{color}{BOLD}{passed}/{N} passed{RESET}")
    sys.exit(0 if passed == N else 1)


if __name__ == "__main__":
    main()
