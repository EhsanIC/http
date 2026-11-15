import socket

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

            if req.route == b"":
                conn.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

            elif req.route == b"echo":
                length = len(req.route_value)
                header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
                conn.sendall(header.encode() + req.route_value)

            elif req.route == b"user-agent" and b"user-agent" in req.headers:

                length = len(str(req.headers[b"user-agent"].decode()))

                header = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {length}\r\n\r\n"
                conn.sendall(header.encode() + req.headers[b"user-agent"])

            else :
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


        except OSError:
            pass   # client vanished mid-exchange; never kill the loop
        finally:
            conn.close()


if __name__ == "__main__":
    main()
