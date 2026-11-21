from ast import While
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

        buffer = b""

        while True:
            raw , rest = parse_request(buffer)
            if raw is None:
                chunk = conn.recv(4096)
                if chunk == b"": break

                buffer += chunk
                continue

            buffer = rest
            req = parse(raw)

            if req is None:
                conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                return

            res = handel(req)
            conn.sendall(res)

            if req.headers.get(b"connection") == b"close":
                return          # finally: closes the socket




    except OSError:
        pass   # client vanished mid-exchange; never kill the loop
    except Exception as e:
        print("error:", e)
    finally:
        conn.close()


def parse_request(data):
    break_location = data.find(b"\r\n\r\n")  # location of first b"\r\n\r\n" | -1

    if break_location == -1: return None, data
    second_head = data[:break_location]
    # b"POST /files/a.txt HTTP/1.1\r\nContent-Length: 5\r\n\r\n
    # helloGET /echo/x HTTP/1.1\r\n\r\n"
    #
    header_break = second_head.split(b"\r\n")
    # b"POST /files/a.txt HTTP/1.1
    # Content-Length: 5
    #
    # helloGET /echo/x HTTP/1.1
    #

    content_length = 0
    for line in header_break[1:]:
        name, sep, value = line.partition(b":")
        if name.strip().lower() == b"content-length":
            content_length = int(value.strip())

    end = break_location + content_length + 4

    if len(data) < end: return None, data

    raw = data[:end]
    buffer = data[end:]

    return raw , buffer


#   Case 1: client supports gzip
#   ─────────────────────────────────────────────
#   Client                              Your server
#     │  GET /echo/abc                      │
#     │  Accept-Encoding: gzip              │
#     │ ──────────────────────────────────> │
#     │                                     │  "gzip" is in the header ✅
#     │  HTTP/1.1 200 OK                    │
#     │  Content-Type: text/plain           │
#     │  Content-Encoding: gzip   ← ADD     │
#     │ <────────────────────────────────── │


#   Case 2: client asks for something unsupported
#   ─────────────────────────────────────────────
#   Client                              Your server
#     │  GET /echo/abc                      │
#     │  Accept-Encoding: invalid-encoding  │
#     │ ──────────────────────────────────> │
#     │                                     │  not "gzip" ❌
#     │  HTTP/1.1 200 OK                    │
#     │  Content-Type: text/plain           │
#     │  (no Content-Encoding)    ← OMIT    │
#     │ <────────────────────────────────── │


# Compute where the request ends:
# end = break_location + 4 + content_length
# You can check this on example 5 by hand. The POST should give end = (end of its headers) + 4 + 5.
# Check that the whole request has arrived: if len(buffer) < end, the body is still on its way. Don’t parse yet. recv more, add it to the buffer, and check again.
# Cut the buffer in two with the slicing you tried earlier:
# raw = buffer[:end] is one request
# buffer = buffer[end:] is the leftover, which you keep for the next loop iteration
# Give raw to parse instead of data, then call handel and send the response as you already do.

if __name__ == "__main__":
    main()
