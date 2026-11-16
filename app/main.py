import socket
import sys
import threading

import os
import app.handlers as handlers

from app.handlers import handel
from app.request import parse


def main():
    print("Logs from your program will appear here!")

    if "--directory" in sys.argv:
        i = sys.argv.index("--directory")
        if i + 1 < len(sys.argv):
            handlers.DIRECTORY = os.path.abspath(sys.argv[i + 1])

    server_socket = socket.create_server(("localhost", 4221))

    while True:
        try:
            conn, addr = server_socket.accept()
        except OSError:
            continue    # a probe/reset connection failed before accept finished

        threading.Thread(target=handle_client, args=(conn,) , daemon=True).start()


def handle_client(conn):
    try:

        data = conn.recv(4096)  # read the request first

        req = parse(data)

        if req is None:
            conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        res = handel(req)
        conn.sendall(res)

    except OSError:
        pass   # client vanished mid-exchange; never kill the loop
    except Exception as e:
        print("error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
