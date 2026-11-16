import os
import socket
import sys
import threading
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


# shared results file — client_test.ps1 collects all suites from it at the end
RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results.txt")


def append_results(passed_names, failed_names):
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        for name in passed_names:
            f.write(f"PASS\t{name}\n")
        for name in failed_names:
            f.write(f"FAIL\t{name}\n")


def run_client(i, barrier, results):
    name = f"Concurrent client {i + 1} is served while another is idle"
    command = '(printf "GET / HTTP/1.1\\r\\n\\r\\n") | nc localhost 4221'

    # everyone waits here, so all N clients hit the server at the same instant
    barrier.wait()

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

    results.append({"name": name, "command": command, "data": data, "elapsed": elapsed})


def main():
    print(f"{YELLOW}Opening an idle connection that sends nothing...{RESET}\n")

    # silent client connects first and blocks a sequential server in recv()
    try:
        idle = socket.create_connection((HOST, PORT), timeout=5)
    except Exception as e:
        print(f"{RED}{BOLD}Could not connect to the server: {e}{RESET}")
        sys.exit(1)

    time.sleep(0.5)

    barrier = threading.Barrier(N)   # all clients released at the same moment
    results = []
    threads = [threading.Thread(target=run_client, args=(i, barrier, results)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    idle.close()

    # print after all clients finished, so output stays clean and ordered
    slowest = 0.0
    passed = 0
    passed_names = []
    failed_names = []
    for r in sorted(results, key=lambda r: r["name"]):
        slowest = max(slowest, r["elapsed"])
        print(f"{CYAN}Test:{RESET}     {r['name']}")
        print(f"{CYAN}Command:{RESET}  {DIM}{r['command']}{RESET}")
        print(f"{CYAN}Output:{RESET}   {r['data']!r} {DIM}({r['elapsed']:.2f}s){RESET}")
        if r["data"] == EXPECTED and r["elapsed"] < MAX_SECONDS:
            print(f"{CYAN}Result:{RESET}   {GREEN}{BOLD}PASS{RESET}\n")
            passed += 1
            passed_names.append(r["name"])
        else:
            print(f"{CYAN}Expected:{RESET} {EXPECTED!r} {DIM}(in under {MAX_SECONDS}s){RESET}")
            print(f"{CYAN}Result:{RESET}   {RED}{BOLD}FAIL{RESET}\n")
            failed_names.append(r["name"])

    append_results(passed_names, failed_names)
    color = GREEN if passed == N else RED
    print(f"{color}{BOLD}{passed}/{N} passed (slowest: {slowest:.2f}s){RESET}")
    sys.exit(0 if passed == N else 1)


if __name__ == "__main__":
    main()
