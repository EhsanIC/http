import socket

from app.handlers import handel
from app.request import parse


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221))

    while True:
        try:
            conn, addr = server_socket.accept()
        except OSError:
            continue    # a probe/reset connection failed before accept finished

        try:
            data = conn.recv(4096)  # read the request first

            req = parse(data)

            if req is None:
                conn.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                continue

            res = handel(req)
            conn.sendall(res)

        except OSError:
            pass   # client vanished mid-exchange; never kill the loop
        finally:
            conn.close()


if __name__ == "__main__":
    main()
